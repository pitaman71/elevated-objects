import { cmp } from './comparison';
import { Domain as BaseDomain } from './domains';
import { Basic as BasicError } from './errors';

type _Syndromes = {
    kind: 'typeMismatch',
    expected: 'boolean' | 'number' | 'string' | 'null' | 'object' | 'array';
} | {
    kind: 'syntaxError',
    tokenType: string
} | {
    kind: 'propertyMismatch',
    properties: Record<string, {
        status: 'good' | 'missing' | 'extra' | 'malformed';
        details?: _Syndromes;
    }>;
};

export type Error = BasicError<_Syndromes['kind']> & _Syndromes;

export type Value<T extends Record<string, any>>  = {
    text?: string,
    errors?: Error[],
    partial?: Partial<T>,
    validated?: T
}

export class Domain<T extends Record<string, any>> extends BaseDomain<Value<T>> {
    domain: BaseDomain<T>;
    constructor(
        domain: BaseDomain<T>
    ) {
        super(`Parseable<${domain.canonicalName}>`);
        this.domain = domain;
    }
    asPartial() { return {
        from: (partial: null|Partial<T>): Value<T>|null => {
            if(partial === null) return null;
            const asProperties = this.domain.asProperties();
            const asString = this.domain.asString();
            const missing = Object.keys(asProperties || {}).reduce<string[]>((missing, propName) => {
                const propSpec = asProperties && propName in asProperties ? asProperties[propName] : undefined;
                if(!propSpec) return missing;
                if(propName in partial || !propSpec.required) return [...missing, propName];
                return missing;
            }, []);
            const validated = missing.length > 0 ? undefined : partial as T;
            const text = !asString || !validated ? undefined : asString.to(validated) || undefined;
            return {
                partial,
                validated,
                text
            }
        }, to: (value: null|Value<T>): Partial<T>|null => {
            if(value === null) return null;
            return value.validated || value.partial || null;
        }
    } }
    asString() { 
        const tAsString = this.domain.asString();
        if(!tAsString) return undefined;
        return {
            to(val: Value<T>|null) {
                if(val === null) return null;
                if(val.text !== undefined) return val.text;
                if(val.validated !== undefined) return tAsString.to(val.validated);
                return null;
            }, from(text: string|null): Value<T>|null {
                if(text === null) return null;
                const errors: Error[] = [];
                const validated = tAsString.from(text, { onError: err => errors.push(err) });
                return {
                    text,
                    errors: errors.length === 0 ? undefined : errors,
                    validated
                } as Value<T>
            }
        }
    }
    cmp(a:Value<T>, b:Value<T>) {
        const tCmp = this.domain.cmp;
        if(!tCmp) return undefined;
        let code = cmp(a.validated,b.validated,tCmp);
        if(code !== 0) return code;
        return 0;
    }
}
export default Value;
