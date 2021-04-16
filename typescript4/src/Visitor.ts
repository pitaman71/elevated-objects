import { Serializable } from './Serializable';

export abstract class Visitor<ExpectedType extends Serializable> {
    abstract beginObject(obj: ExpectedType): void;
    abstract endObject(obj: ExpectedType): void;

    abstract verbatim<DataType>(target: any, propName: string): void;
    abstract primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void;
    abstract scalar<ObjectType extends Serializable>(target: any, propName: string): void;
    abstract array<ElementType extends Serializable>(target: any, propName: string): void;
}
