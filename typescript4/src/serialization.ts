import * as traversal from './traversal';
import { factories } from './construction';

export abstract class Serializable {
    getFactory: any

    abstract marshal(visitor: traversal.Visitor<this>): void;

    getGlobalId(): number|string|null { return null; }

    toString(): string {
        const globalId = this.getGlobalId();
        return `${this.getFactory()} \"${globalId}\"`;
    }
}
