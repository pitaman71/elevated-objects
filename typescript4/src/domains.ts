export abstract class Domain<ValueType> {
    abstract fromString(text: string): ValueType;
    abstract toString(value: ValueType): string;
    abstract cmp(a: ValueType, b:ValueType): undefined|-1|0|1;
    abstract make(): ValueType;
    abstract enumerable(maxCount: number): boolean;
    abstract enumerate(maxCount: number, ascending: boolean): Generator<ValueType>;
    abstract random(... history: ValueType[]): undefined|ValueType;
}

export function makeValueClass<ValueType>(
    domain: Domain<ValueType>
) {
    return class Idiomatic {
        value?: ValueType;
        toString() { return this.value === undefined ? '' : domain.toString(this.value) }
        protected constructor(value?: ValueType) { this.value = value }
        static fromString(value: string)  { return new this(domain.fromString(value)); }
        static cmp(a: Idiomatic, b: Idiomatic) { return a.value === undefined || b.value === undefined ? undefined : domain.cmp(a.value, b.value) }
        static make(): Idiomatic { return new Idiomatic(domain.make()) }
    }
}
