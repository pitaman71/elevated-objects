import { factories } from './construction';
import { Node as SchemaNode } from './schema';
import { Serializable } from './serialization';
import { Visitor } from './traversal';

export type JSONValue = boolean | number | string | null | { [key: string]: JSONValue|undefined } | Array<JSONValue>;

export interface Error {
    type?: {
        expected: 'boolean' | 'number' | 'string' | 'null' | 'object' | 'array'        
    },
    format?: {
        expected?: { tokenType: string },
        atCharacter?: number
    },
    properties?: { [propName:string]: {
        status: 'good'|'missing'|'extra'|'malformed',
        details?: Error
    } }
};

export abstract class Domain<ValueType> {
    asSchema(): undefined|SchemaNode<any> { return undefined; }
    asJSON(): undefined|{
        from(json: JSONValue, options?: { onError?: (error: Error) => void }): ValueType|null;
        to(value: ValueType|null, options?: { onError?: (error: Error) => void }): JSONValue;
    } { return undefined }
    asProperties(): undefined|{
        names: string[],
        domain: (propName: string) => undefined|Domain<any> 
    } { return undefined }
    asEnumeration(maxCount: number): undefined|{
        forward(): Generator<ValueType>;    
        backward(): Generator<ValueType>;    
    } { return undefined }
    abstract asString(format?: string): undefined|{
        from(text: string, options?: { onError?: (error: Error) => void }): ValueType|null;
        to(value: ValueType, options?: { onError?: (error: Error) => void }): string
    };
    abstract cmp(a: ValueType, b:ValueType): undefined|-1|0|1;
}

export type getValueType<T> = T extends Domain<infer U> ? U : never;

export class Samples<ValueType> {
    _values: ValueType[];

    constructor(...values_: ValueType[]) {
        this._values = [ ...values_ ];
    }

    random() {
        const index = Math.floor(Math.random() * this._values.length);
        return this._values[index];
    }
}

export function makeValueClass<ValueType>(
    classSpec: string,
    domain: Domain<ValueType>
) {
    return class _Value extends Serializable {
        value?: ValueType;
        static Factory = factories.concrete<_Value>(classSpec, () => new _Value());
        getFactory = () => _Value.Factory;
        getGlobalId(): number|string|null { return null; }
        marshal(visitor: Visitor<this>): void {
            visitor.begin(this);
            visitor.primitive(this, 'value')
            visitor.end(this);
        }
        toString() { return this.value !== undefined && domain.asString()?.to(this.value) || '' }
        static from(value?: ValueType) {
            const result = new _Value();
            result.value = value;
            return result;
        }
        static fromString(text: string)  { return _Value.from(domain.asString()?.from(text) || undefined); }
        static cmp(a: _Value, b: _Value) { return a.value === undefined || b.value === undefined ? undefined : domain.cmp(a.value, b.value) }
        static domain() { return domain }
    }
}
