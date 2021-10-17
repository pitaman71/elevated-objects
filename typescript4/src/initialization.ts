import { Serializable } from './serialization';
import { Reference } from './references';
import { Factory } from './construction';
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
        target: Serializable,
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void
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

    reference<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void {
        const newValue = this.initializers.reduce(
            (result: any, initializer: any) => initializer[propName] || result
        , undefined);
        if(newValue !== undefined) {
            const target:any = this.obj;
            target[propName] = Reference.from(newValue);
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