import { throws } from 'node:assert';
import { Serializable } from './serialization';
import { Visitor } from './traversal';

export class Initializer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    factory: Factory<ExpectedType>;
    initializers: any[];
    obj?: ExpectedType;

    begin(obj: ExpectedType): void { this.obj = obj; }
    end(obj: ExpectedType): void {}
    owner(target: ExpectedType, ownerPropName: string): void {}

    constructor(
        factory: Factory<ExpectedType>,
        ...initializers: any[]
    ) {
        this.factory = factory;
        this.initializers = initializers;
    }

    clone(... initializers: any[]): Serializable {
        const result = this.factory.make();
        const initializer = new Initializer(this.factory, ... initializers);
        result.marshal(initializer);
        return result;
    }

    verbatim<DataType>(
        getValue: (target: ExpectedType) => any,
        setValue: (target: ExpectedType, value: any) => void
    ): void {
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer || result
        , undefined);
        if(this.obj && newValue !== undefined)
            setValue(this.obj, newValue);
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer[propName] || result
        , undefined);
        if(newValue !== undefined) {
            const typedValue = (typeof(newValue) === 'string')  && fromString ? fromString(newValue) : newValue;
            target[propName] = typedValue;
        }
    }

    scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        const newValues = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        ).map((initializer: any) => initializer[propName]);
        if(newValues.length == 1) {
            if(this.obj) {
                const tmp = <any>this.obj;
                tmp[propName] = newValues[0];
            }
        } else if(newValues.length > 1) {
            if(this.obj) {
                const tmp = <any>this.obj;
                tmp[propName] = this.clone(... newValues);
            }
        }
    }

    array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        const hasProperty = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        );
        const maxLength = hasProperty.reduce(
            (result: number, initializer: any) => 
                Math.max(initializer[propName].length, result)
        , 0);
        if(maxLength > 0) {
            const newArrayValue = [ ... Array(maxLength).keys() ].reduce(
                (arrayValue: ElementType[], index: number) => {
                    const longEnoughArrays = hasProperty.filter(
                        (initializer: any) => index < initializer[propName].length
                    );
                    const elementValues = longEnoughArrays.reduce(
                        (collected: ElementType[], initializer: any) => 
                        [ ... collected, initializer[propName][index]]
                    , []);
                    return elementValues.length == 0 
                        ? arrayValue 
                        : elementValues.length == 1
                        ? [ ... arrayValue, elementValues[0] ]
                        : [ ... arrayValue, this.clone(... elementValues) ];
                }
            , []);
            if(this.obj) {
                const tmp = <any>this.obj;
                tmp[propName] = newArrayValue;
            }
        }
    }

    map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        const hasProperty = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        );
        const allKeys = hasProperty.reduce(
            (allKeys: Array<string>, initializer:any) => 
                Object.getOwnPropertyNames(initializer[propName]).reduce(
                    (allKeys: Array<string>, key: string) =>
                        key in allKeys ? allKeys : [ ... allKeys, key ]
                , allKeys)
        , []);
        const newValue = allKeys.reduce( (newValue: any, key: string) => {
            const hasKey = hasProperty.filter(
                (initializer: any) => initializer[propName].hasOwnProperty(key)
            );
            const elementValues = hasKey.reduce(
                (collected: ElementType[], initializer: any) => 
                    [ ... collected, initializer[propName][key]]
            , []);
            const elementValue: ElementType = 
                elementValues.length == 0 ? undefined :
                elementValues.length == 1 ? elementValues[1] :
                this.clone(... elementValues);
            return { ... newValue, [propName]: elementValue };
        }, {});
    }

    init(target: ExpectedType): any {
        target.marshal(this);
    }
}

type Allocator<ExpectedType extends Serializable> = (factory: Factory<ExpectedType>, initializer?: any) => ExpectedType;

export class Factory<ExpectedType extends Serializable> {
    classSpec: string;
    allocators: { [key: string]: Allocator<ExpectedType> };

    static abstract<ExpectedType extends Serializable>(classSpec: string) {
        const result = new Factory<ExpectedType>(classSpec);
        return result;
    }

    static concrete<ExpectedType extends Serializable>(classSpec: string, 
        allocator: Allocator<ExpectedType>
    ) {
        const result = new Factory<ExpectedType>(classSpec);
        result.allocators = { [classSpec]: allocator };
        return result;
    }

    static derived<ExpectedType extends Serializable>(classSpec: string, 
        allocator: Allocator<ExpectedType>,
        parentFactories: Factory<any>[]
    ) {
        const result = new Factory<ExpectedType>(classSpec);
        result.allocators = { [classSpec]: allocator };
        parentFactories.forEach((parentFactory: Factory<any>) => {
            parentFactory.allocators = { 
                ... parentFactory.allocators,
                ... result.allocators
            };
        });
        return result;
    }

    constructor(classSpec: string) {
        this.classSpec = classSpec;
        this.allocators = {};
    }

    getClassSpec() {
        return this.classSpec;
    }

    make(classSpec?: string): ExpectedType {
        if(classSpec === undefined) {
            classSpec = this.classSpec;
        }

        if(!Object.getOwnPropertyNames(this.allocators).includes(classSpec)) {
            throw new Error(`Object of type ${classSpec}is not compatible with ${Object.getOwnPropertyNames(this.allocators)}`);
        }
        const result = this.allocators[classSpec](this);
        result.getFactory = () => this;
        return result
    }
}

export class Factories {
    specToBuilder: { [key: string]: Factory<Serializable> };

    constructor() {
        this.specToBuilder = {};
    }
    
    register<ExpectedType extends Serializable>(classSpec: string, factoryMaker: () => Factory<Serializable>): Factory<ExpectedType> {
        if(!Object.getOwnPropertyNames(this.specToBuilder).includes(classSpec)) {
            this.specToBuilder[classSpec] = factoryMaker();
        }
        const factory: any = this.specToBuilder[classSpec];
        return factory;
    }

    concrete<ExpectedType extends Serializable>(classSpec: string, objectMaker: () => ExpectedType): Factory<ExpectedType> {
        return this.register(classSpec, () => Factory.concrete<Serializable>(classSpec, objectMaker));
    }

    hasClass(classSpec?: string): boolean {
        return !!classSpec && this.specToBuilder.hasOwnProperty(classSpec);
    }

    getFactory(classSpec: string): Factory<any> {
        return this.specToBuilder[classSpec];
    }

    make(classSpec: string): Serializable {
        return this.specToBuilder[classSpec.toString()].make();
    }
}

export const factories = new Factories();

export class Builder<ExpectedType extends Serializable, DoneType> {
    factory: Factory<ExpectedType>;
    whenDone: (initializer?: any) => DoneType;
    built: ExpectedType;

    constructor(
        factory: Factory<ExpectedType>,
        whenDone: (initializer?: any) => DoneType = (x) => x,
        built?: ExpectedType
    ) {
        this.factory = factory;
        this.whenDone = whenDone;
        this.built = built || factory.make();
    }

    getClassSpec() { return this.factory.classSpec; }

    done(finisher: (built: ExpectedType) => ExpectedType = (x) => x): DoneType {
        return this.whenDone(finisher(this.built));
    }
}
