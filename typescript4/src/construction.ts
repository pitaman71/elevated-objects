import { Serializable } from './serialization';
import { Visitor } from './traversal';

export class Factory {
    specToBuilder: { [key: string]: Builder<Serializable> };

    constructor() {
        this.specToBuilder = {};
    }
    
    addBuilders(builders: Builder<any>[]) {
        builders.forEach((builder: Builder<any>) => {
            const classSpec = builder.getClassSpec();
            if(Object.getOwnPropertyNames(this.specToBuilder).includes(classSpec)) {
                throw new Error(`Duplicate definition of class_spec ${classSpec}`);
            }
            this.specToBuilder[classSpec] = builder;
        });
    }

    hasClass(classSpec?: string): boolean {
        return !!classSpec && this.specToBuilder.hasOwnProperty(classSpec);
    }

    getBuilder(classSpec: string): Builder<any> {
        return this.specToBuilder[classSpec];
    }

    getBuilderOf(obj: Serializable): Builder<any> {
        return obj.__builder__;
    }

    make(classSpec: string): Serializable {
        return this.specToBuilder[classSpec.toString()].make();
    }
}

export class Initializer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    builder: Builder<ExpectedType>;
    initializers: any[];
    obj?: ExpectedType;

    begin(obj: ExpectedType, parentPropName?: string): void { this.obj = obj; }
    end(obj: ExpectedType): void {}
    owner(target: ExpectedType, ownerPropName: string): void {}

    constructor(builder: Builder<ExpectedType>, ...initializers: any[]) {
        this.builder = builder;
        this.initializers = initializers;
    }

    clone(... initializers: any[]): Serializable {
        const result = this.builder.make();
        const initializer = new Initializer(this.builder, ... initializers);
        result.marshal(initializer);
        return result;
    }

    verbatim<DataType>(
        target: any, 
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>
    ): void {
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer || result
        , undefined);
        if(newValue !== undefined)
            setValue(target, newValue);
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
        elementBuilder: Builder<ElementType>,
        target: any, 
        propName: string        
    ): void {
        const newValues = this.initializers.filter(
            (initializer: any) => initializer[propName] !== undefined
        ).map((initializer: any) => initializer[propName]);
        if(newValues.length == 1) {
            target[propName] = newValues[0];
        } else if(newValues.length > 1) {
            target[propName] = elementBuilder.clone(... newValues);
        }
    }

    array<ElementType extends Serializable>(
        elementBuilder: Builder<ElementType>,
        target: any, 
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
                    return elementValues.length 
                        ? arrayValue 
                        : [ ... arrayValue, elementBuilder.clone(... elementValues) ];
                }
            , []);
            target[propName] = newArrayValue;
        }
    }

    map<ElementType extends Serializable>(
        elementBuilder: Builder<ElementType>,
        target: any, 
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
                elementBuilder.clone(... elementValues);
            return { ... newValue, [propName]: elementValue };
        }, {});
    }

    init(target: ExpectedType): any {
        target.marshal(this);
    }
}

export class Builder<ExpectedType extends Serializable> {
    factory: Factory;
    classSpec: string
    allocator: (initializer?: any) => ExpectedType;
    whenDone: (initializer?: any) => ExpectedType;
    built: ExpectedType;

    constructor(
        factory: Factory,
        classSpec: string,
        allocator: (initializer?: any) => ExpectedType,
        whenDone: (initializer?: any) => ExpectedType = (x) => x,
        built?: ExpectedType
    ) {
        this.factory = factory;
        this.classSpec = classSpec
        this.allocator = allocator;
        this.whenDone = whenDone;
        this.built = built || allocator();
        this.built.__builder__ = this;
    }

    getClassSpec() { return this.classSpec; }

    make(initializer?: any): ExpectedType {
        const result = this.allocator(initializer);
        result.__builder__ = this;
        return result;
    }

    clone(...initializers: Array<Serializable>): ExpectedType {
        const result = this.allocator();
        const initializer = new Initializer(this, ...initializers);
        result.marshal(initializer);
        return result;
    }

    done(finisher: (built: ExpectedType) => Serializable = (x) => x): Serializable {
        return finisher(this.whenDone(this.built));
    }
}
