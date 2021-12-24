import { factories } from './construction';
import { Serializable } from './serialization';
import { Visitor } from './traversal';

export abstract class Domain<ValueType> {
    abstract fromString(text: string, format?: string): ValueType;
    abstract toString(value: ValueType, format?: string): string;
    abstract cmp(a: ValueType, b:ValueType): undefined|-1|0|1;
    abstract make(): ValueType;
    abstract enumerable(maxCount: number): boolean;
    abstract enumerate(maxCount: number, ascending: boolean): Generator<ValueType>;
    abstract random(... history: ValueType[]): undefined|ValueType;
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
        toString() { return this.value === undefined ? '' : domain.toString(this.value) }
        static from(value?: ValueType) {
            const result = new _Value();
            result.value = value;
            return result;
        }
        static fromString(text: string)  { return _Value.from(domain.fromString(text)); }
        static cmp(a: _Value, b: _Value) { return a.value === undefined || b.value === undefined ? undefined : domain.cmp(a.value, b.value) }
        static domain() { return domain }
    }
}

export class Aggregate<ValueType> implements Domain<ValueType> {
    proto: Map<keyof ValueType, Domain<any>>;
    members: string[];

    constructor(proto: { [propName: string]: Domain<any>}) {
        this.proto = new Map();
        Object.getOwnPropertyNames(proto).forEach(key => {
            this.proto.set(key as keyof ValueType, proto[key]);
        });
        this.members = Object.getOwnPropertyNames(proto);
    }

    fromString(text: string, format?: string): ValueType {
        const parsed = JSON.parse(text);
        if(!parsed) throw new Error(`Cannot parse "${text}"`);
        const result: any = {};
        this.members.forEach(member => {
            result[member] = parsed[member];
        })
        return result;
    }

    toString(value: ValueType, format?: string): string {
        const result: any = {};
        this.members.forEach(member => {
            result[member] = value[member as keyof ValueType];
        });
        return JSON.stringify(result);
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
    make(): ValueType {
        const result: any = {};
        this.members.forEach(member => {
            result[member] = this.proto.get(member as keyof ValueType)?.make();
        });        
        return result;
    }
    enumerable(maxCount: number): boolean {
        return false;
    }
    enumerate(maxCount: number, ascending: boolean): Generator<ValueType> {
        throw new Error('Aggregates are not enumerable');
    }

    random(... history: ValueType[]): undefined|ValueType {
        const result: any = {};
        this.members.forEach(member => {
            result[member] = this.proto.get(member as keyof ValueType)?.make();
        });        
        return result;
    }
}