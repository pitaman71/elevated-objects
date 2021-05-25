import * as traversal from './traversal';
import * as JSONMarshal from './JSONMarshal';

export abstract class Serializable {
    __builder__: any

    abstract marshal(visitor: traversal.Visitor<this>): void;

    getGlobalId(): number|string|null { return null; }
}
