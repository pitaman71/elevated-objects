import { Builder } from './construction';
import { Serializable } from './Serializable';

export abstract class Visitor<ExpectedType extends Serializable> {
    abstract begin(obj: ExpectedType): void;
    abstract end(obj: ExpectedType): void;

    abstract verbatim<DataType>(
        target: any, 
        propName: string,
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>        
    ): void;
    abstract primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void;
    abstract scalar<ElementType extends Serializable>(
        elementBuilder: Builder<ElementType>, 
        target: any, 
        propName: string
    ): void;
    abstract array<ElementType extends Serializable>(
        elementBuilder: Builder<ElementType>, 
        target: any, 
        propName: string
    ): void;
    abstract map<ElementType extends Serializable>(
        elementBuilder: Builder<ElementType>, 
        target: any, 
        propName: string
    ): void;
}
