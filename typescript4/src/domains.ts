import { factories } from './construction';
import { Node as SchemaNode } from './schema';
import { Serializable } from './serialization';
import { Visitor } from './traversal';

export type JSONValue = boolean | number | string | null | { [key: string]: JSONValue|undefined } | Array<JSONValue>;

export abstract class Domain<ValueType> {
    asJSON(): undefined|{
        schema(): SchemaNode<any>;
        from(json: JSONValue): ValueType|null;
        to(value: ValueType|null): JSONValue;
    } { return undefined }
    abstract asString(format?: string): undefined|{
        from(text: string): ValueType|null;
        to(value: ValueType): string
    };
    abstract asEnumeration(maxCount: number): undefined|{
        forward(): Generator<ValueType>;    
        backward(): Generator<ValueType>;    
    }
    abstract asColumns(): undefined| {
        getColumnNames(): string[];
    }
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

export class Aggregate<ValueType> extends Domain<ValueType> {
    proto: Map<keyof ValueType, Domain<any>>;
    members: string[];

    constructor(proto: { [propName: string]: Domain<any>}) {
        super();
        this.proto = new Map();
        Object.getOwnPropertyNames(proto).forEach(key => {
            this.proto.set(key as keyof ValueType, proto[key]);
        });
        this.members = Object.getOwnPropertyNames(proto);
    }

    asString(format?: string) {
        const target = this;
        return new class {
            from(text: string): ValueType {
                const parsed = JSON.parse(text);
                if(!parsed) throw new Error(`Cannot parse "${text}"`);
                const result: any = {};
                target.members.forEach(member => {
                    result[member] = parsed[member];
                })
                return result;
            }

            to(value: ValueType): string {
                const result: any = {};
                target.members.forEach(member => {
                    result[member] = value[member as keyof ValueType];
                });
                return JSON.stringify(result);
            }
        }
    }

    asColumns() { 
        const target=this;
        return new class {
            getColumnNames(): string[] {
                let result: string[] = [];
                target.members.forEach(member => {
                    const asColumns = target.proto.get(member as keyof ValueType)?.asColumns();
                    if(!asColumns)
                        result = [ ...result, member ];
                    else
                        result = [ ...result, ...asColumns.getColumnNames().map(sub => `${member}.${sub}`) ];
                });
                return result;
            }
        } 
    }

    cmp(a: ValueType, b:ValueType): undefined|-1|0|1 {
        this.members.forEach(member => {
            if(a[member as keyof ValueType] === undefined && b[member as keyof ValueType] !== undefined) return -1;
            if(a[member as keyof ValueType] !== undefined && b[member as keyof ValueType] === undefined) return +1;
            if(a[member as keyof ValueType] !== undefined && b[member as keyof ValueType] !== undefined) {
                if(a[member as keyof ValueType] < b[member as keyof ValueType]) return -1;
                if(a[member as keyof ValueType] > b[member as keyof ValueType]) return +1;
            }
        });
        return 0;
    }

    asEnumeration(maxCount: number) {
        return undefined;
    }
}
