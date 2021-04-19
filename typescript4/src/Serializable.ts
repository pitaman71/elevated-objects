import { Visitor } from './traversal';
import * as JSONMarshal from './JSONMarshal';

export abstract class Serializable {
    abstract getClassSpec(): string;
    abstract marshal(visitor: Visitor<this>): void;
    abstract id(): any;
}
