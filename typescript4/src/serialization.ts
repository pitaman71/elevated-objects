import * as traversal from './traversal';

export abstract class Serializable {
    getFactory: any

    abstract marshal(visitor: traversal.Visitor<this>): void;

    getGlobalId(): number|string|null { return null; }

    toString(): string {
        const globalId = this.getGlobalId();
        return `${this.getFactory()} \"${globalId}\"`;
    }
}

export class Reference<ValueType extends Serializable> {
    _ref: string|number|null = null;
    _def: ValueType|null = null;

    isNotNull() { return this._ref !== null || this._def !== null }
    pointsTo(obj: ValueType) { return this._def === obj || (this._ref !== null && obj.getGlobalId() === this._ref) }
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

    static from<ValueType extends Serializable>(obj: string|number|null|ValueType) {
        const result = new Reference<ValueType>();
        if(typeof(obj) === 'string' || typeof(obj) === 'number') {
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
