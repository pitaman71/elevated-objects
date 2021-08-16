import { Factory } from './construction';
import { Serializable } from './serialization';

export abstract class Visitor<ExpectedType extends Serializable> {
    abstract begin(obj: ExpectedType): void;
    abstract end(obj: ExpectedType): void;

    abstract owner(target: ExpectedType, ownerPropName: string): void;
    abstract verbatim<DataType>(
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void
    ): void;
    abstract primitive<PropType>(
        target: any, 
        propName: string, 
        fromString?: (initializer:string) => PropType): void;
    abstract scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void;
    abstract array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void;
    abstract map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void;
}
