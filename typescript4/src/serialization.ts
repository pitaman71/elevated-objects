import * as traversal from './traversal';

export abstract class Serializable {
    __factory__: any

    abstract marshal(visitor: traversal.Visitor<this>): void;
    abstract getClassSpec(): string;

    getGlobalId(): number|string|null { return null; }

    toString(): string {
        const globalId = this.getGlobalId();
        return `${this.getClassSpec()} \"${globalId}\"`;
    }
}
