import { Serializable } from './Serializable';
import { Visitor } from './traversal';

import * as JSONMarshal from './JSONMarshal';

export class Factory {
    specToBuilder: { [key: string]: Builder<Serializable> };

    constructor() {
        this.specToBuilder = {};
    }
    
    addValueMakers(prefix: Array<string>, valueMakers: { [key: string]: () => Serializable }) {
        Object.getOwnPropertyNames(valueMakers).forEach((suffix: string) => {
            const classSpec = [ ... prefix, ... suffix.split('.') ].join('.');
            if(this.specToBuilder.hasOwnProperty(classSpec)) {
                throw new Error(`Duplicate definition of class_spec ${classSpec}`);                
            }
            const ctor = valueMakers[suffix];
            const tmp = ctor();
            this.specToBuilder[classSpec] = new Builder(ctor);
        })
    }

    getClassSpec(obj: any): string {
        return obj.getClassSpec();
    }

    hasClass(classSpec: any): boolean {
        return classSpec && this.specToBuilder.hasOwnProperty(classSpec.toString());
    }

    make(classSpec: any): Serializable {
        const builder = this.specToBuilder[classSpec.toString()];
        return builder.make();
    }
}

export class Initializer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    initializers: any[];
    obj?: ExpectedType;

    begin(obj: ExpectedType, parentPropName?: string): void { this.obj = obj; }
    end(obj: ExpectedType): void {}

    constructor(...initializers: any[]) {
        this.initializers = initializers;
    }

    verbatim<DataType>(
        target: any, 
        propName: string,
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
                    const elementValue: ElementType = elementValues.length > 0 && 
                        elementValues[0].clone(... elementValues);
                    return [ ... arrayValue, elementValue ];
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
    allocator: (initializer?: any) => ExpectedType;

    constructor(allocator: (initializer?: any) => ExpectedType) {
        this.allocator = allocator;
    }

    make(initializer?: any): ExpectedType {
        return this.allocator(initializer);
    }

    clone(...initializers: Array<Serializable>): Serializable {
        const result = this.allocator();
        const initializer = new Initializer(...initializers);
        result.marshal(initializer);
        return result;
    }
}
