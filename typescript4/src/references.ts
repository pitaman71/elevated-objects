import { factories } from './construction';
import { Serializable } from './serialization';
import * as traversal from './traversal';

export class Reference<ValueType extends Serializable> extends Serializable {
    _ref: string|number|null = null;
    _def: ValueType|null = null;

    static ClassSpec = 'elevated-objects.Reference';
    static Factory = factories.concrete<Reference<any>>(Reference.ClassSpec, () => new Reference<any>());
    toString() {
        return `@${Reference.ClassSpec} ${this._ref} ${this._def?.toString()}`
    }
    getFactory = () => Reference.Factory;
    getGlobalId() { return this._ref }
    marshal(visitor:traversal.Visitor<this>) {
        visitor.begin(this);
        visitor.verbatim(
            (target) => {
                return { __id__: (<this>target)._ref };
            },
            (target, value) => {
                (<this>target)._ref = value.__id__;
            }
        )
        visitor.end(this);
    }
    isNotNull() { return this._ref !== null || this._def !== null }
    pointsTo(obj: Reference<ValueType>|ValueType|undefined|null) { 
        if(obj === undefined || obj === null) {
            return false;
        } else if(obj instanceof Reference) {
            return (
                (obj.getGlobalId() !== null && obj.getGlobalId() === this.getGlobalId())
                || (obj._def !== null && obj._def === this._def)
            );
        } else {
            return (
                obj !== undefined && obj !== null && 
                (this._def === obj || (this._ref !== null && obj.getGlobalId() === this._ref))
            );
        }
    }
    ref() { return this._ref }
    def(fetch: (ref: string|number) => Promise<ValueType>): Promise<ValueType> {
        if(this._def !== null) {
            return Promise.resolve(this._def);
        } else if(this._ref !== null) {
            return fetch(this._ref).then(def => {
                this._def = def;
                return def;
            })
        } else {
            return Promise.reject(`NULL pointer reference`);
        }
    }
    static fromNull<ValueType extends Serializable>() {
        const result = new Reference<ValueType>();
        result._ref = null;
        result._def = null;
        return result;
    }

    static from<ValueType extends Serializable>(obj: string|number|null|ValueType|Reference<ValueType>) {        
        const result = new Reference<ValueType>();
        if(obj === undefined) {
            throw new Error('undefined passsed to Reference.from')
        }
        if(obj instanceof Reference) {
            result._ref = obj._ref;
            result._def = obj._def;
        } else if(typeof(obj) === 'string' || typeof(obj) === 'number') {
            result._ref = obj;
        } else if(obj === null) {
            result._ref = null;            
        } else {
            result._ref = obj.getGlobalId();
            result._def = obj;
        }
        return result;
    }
    
    collect(direction: (def: ValueType) => Reference<ValueType>, fetch: (ref: string|number) => Promise<ValueType>, until: (def: ValueType) => boolean): Promise<Array<ValueType>> {
        if(this._ref === null && this._def === undefined) {
            return Promise.resolve([]);
        }
        
        const defPromise = this._def !== undefined? Promise.resolve(this._def) : this._ref !== null ? fetch(this._ref) : Promise.reject('unreachable code');
        return defPromise.then((def) => {
            if(def === null) {
                return [];
            } else if(until(def)) {
                return [];
            } else {
                const nextRef = direction(def);
                if(nextRef !== null) {
                    return nextRef.collect(direction, fetch, until)
                    .then((prevArray) => { return [ def, ... prevArray ] });
                } else {
                    return [ def ];
                }
            }    
        })
    }

}
