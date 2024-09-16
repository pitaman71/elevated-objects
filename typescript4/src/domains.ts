import { factories } from './construction';
import { Node as SchemaNode } from './schema';
import { Serializable } from './serialization';
import { Visitor } from './traversal';

export type JSONValue = boolean | number | string | null | { [key: string]: JSONValue|undefined } | Array<JSONValue>;

/**
 * Interface for returning details about a parse error
 */
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

/**
 * Abstract base for classes that model introspectable datatypes.
 */
export abstract class Domain<ValueType> {
    /** return the schema representation of this introspectable datatype */
    asSchema(): undefined|SchemaNode<any> { return undefined; }

    /** returns methods for parsing an object from JSON or printing an object to JSON */
    asJSON(): undefined|{
        from(json: JSONValue, options?: { onError?: (error: Error) => void }): ValueType|null;
        to(value: ValueType|null, options?: { onError?: (error: Error) => void }): JSONValue;
    } { return undefined }

    /** 
     * If this is an aggregate or aggregate-like datatype, 
     * calling this method will return a list of property names and a map 
     * from property names to subdomains 
     */
    asProperties(): undefined|{
        names: string[],
        domain: (propName: string) => undefined|Domain<any> 
    } { return undefined }

    /**
     * If this domain has a countable number of legal values,
     * calling this method will return two methods for iterating
     * through that set of legal values in forward or backward order,
     * according to the domain's natural ordering of values.
     */
    asEnumeration(maxCount: number): undefined|{
        forward(): Generator<ValueType>;    
        backward(): Generator<ValueType>;    
    } { return undefined }

    /**
     * If this domain has a string representation, calling this
     * method will return methods for converting a value to or
     * from string representation.
     */
    abstract asString(format?: string): undefined|{
        from(text: string, options?: { onError?: (error: Error) => void }): ValueType|null;
        to(value: ValueType, options?: { onError?: (error: Error) => void }): string
    };

    /**
     * Compares the two provided values according to the domain's natural sort
     * order, if one exists.
     * @returns -1 if a is ordered before b
     * @returns 0 if a and b have the same position in the order (equivalent value)
     * @returns +1 if b is ordered before a
     * @returns undefined if the order of a and b cannot be determined
     */
    abstract cmp(a: ValueType, b:ValueType): undefined|-1|0|1;
}

export type getValueType<T> = T extends Domain<infer U> ? U : never;

/**
 * @deprecated
 */
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

/**
 * @deprecated
 */
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
