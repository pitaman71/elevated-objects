import { Visitor } from './Visitor';
import * as JSONMarshal from './JSONMarshal';

export abstract class Serializable {
    abstract getClassSpec(): string;
    abstract marshal(visitor: Visitor<this>): void;

    clone(...initializers: any[]): this { 
        const result:this = new (<any>this.constructor);
        result.overlay(...initializers);
        return result;
    }

    overlay(...initializers: any[]) {
        const initializer = new JSONMarshal.Initializer(...initializers);
        initializer.init(this);
    }
}
