import { Factory } from './construction';
import * as serialization from './serialization';
import * as traversal from './traversal';

type Result = -1 | 0 | 1 | undefined;

class Comparator<ExpectedType extends serialization.Serializable> implements traversal.Visitor<ExpectedType> {
    a: any;
    b: any;
    result: Result;

    constructor(a: ExpectedType, b: ExpectedType) {
        this.a = a;
        this.b = b;
        this.result = undefined;
    }

    begin(obj: ExpectedType, parentPropName?: string): Result {
        this.result = 0;
        return this.result;
    }

    end(obj: ExpectedType): Result {
        return this.result;
    }

    owner(target: ExpectedType, ownerPropName: string) {        
    }

    verbatim<DataType>(
        target: serialization.Serializable,
        getValue: (target: serialization.Serializable) => any,
        setValue: (target: serialization.Serializable, value: any) => void
    ): Result {
        if(this.result !== 0) {
            return this.result;
        }
        
        const aProp = getValue(this.a);
        const bProp = getValue(this.b);
        if(aProp === undefined && bProp !== undefined) {
            this.result = -1;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = 1;
        } else if(aProp === undefined && bProp === undefined) {
            // pass
        } else if(aProp < bProp) {
            this.result = -1;
        } else if(aProp > bProp) {
            this.result = 1;
        }
        return this.result;
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): Result {
        if(this.result !== 0) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = -1;
        } else if(aHasProp && !bHasProp) {
            this.result = 1;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp === undefined && bProp !== undefined) {
            this.result = -1;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = 1;
        } else if(aProp === undefined && bProp === undefined) {
            // pass
        } else if(aProp < bProp) {
            this.result = -1;
        } else if(aProp > bProp) {
            this.result = 1;
        }
        return this.result;
    }

    reference<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        if(this.result !== 0) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = -1;
        } else if(aHasProp && !bHasProp) {
            this.result = 1;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp._ref < bProp._ref) {
            this.result = -1;
        } else if(aProp._ref > bProp._ref) {
            this.result = 1;
        } else if(aProp._def < bProp._def) {
            this.result = -1;
        } else if(aProp._def > bProp._def) {
            this.result = 1;
        }
        return this.result;
    }

    compare_elements<ElementType extends serialization.Serializable>(
        a_prop: serialization.Serializable,
        b_prop: serialization.Serializable
    ) {
        if(a_prop.getGlobalId() === null && b_prop.getGlobalId() === null) {
            const sub = new Comparator(a_prop, b_prop);
            a_prop.marshal(sub);
            if(sub.result !== 0) {
                this.result = sub.result;
            }
        } else if(a_prop.getGlobalId() === null && b_prop.getGlobalId() !== null) {
            this.result = -1;
        } else if(a_prop.getGlobalId() !== null && b_prop.getGlobalId() === null) {
            this.result = 1;
        } else if((a_prop.getGlobalId() || 0) < (b_prop.getGlobalId() || 0)) {
            this.result = -1;
        } else if((a_prop.getGlobalId() || 0) >(b_prop.getGlobalId() || 0)) {
            this.result = -1;
        }
    }

    scalar<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        if(this.result !== 0) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = -1;
        } else if(aHasProp && !bHasProp) {
            this.result = 1;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp === undefined && bProp === undefined) {
            return this.result;
        } else if(aProp === undefined && bProp !== undefined) {
            this.result = -1;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = 1;
        } else {
            this.compare_elements(aProp, bProp);
        }
        if(this.result === undefined) {
            this.result = 0;
        }
        return this.result;
    }

    array<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = -1;
        } else if(aHasProp && !bHasProp) {
            this.result = 1;
        }
        if(this.a.length < this.b.length) {
            this.result = -1;
        } else if(this.a.length > this.b.length) {
            this.result = 1;
        }

        this.a[propName].forEach((aProp: serialization.Serializable, index: number) => {
            const bProp = this.b[propName][index];
            if(this.result === undefined) {
                this.compare_elements(aProp, bProp);
            }
        });
        if(this.result === undefined) {
            this.result = 0;
        }
        return this.result;
    }

    map<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = -1;
        } else if(aHasProp && !bHasProp) {
            this.result = 1;
        }
        const aKeys = Object.getOwnPropertyNames(this.a[propName]);
        const bKeys = Object.getOwnPropertyNames(this.b[propName]);
        if(aKeys < bKeys) {
            this.result = -1;
        } else if(aKeys > bKeys) {
            this.result = 1;
        }
        aKeys.forEach((key: string) => {
            if(this.result === undefined) {
                this.compare_elements(this.a[propName][key], this.b[propName][key]);
            }
        });
        if(this.result === undefined) {
            this.result = 0;
        }
        return this.result;
    }
}

export function cmp<DataType>(a: DataType|undefined, b:DataType|undefined, comparator?: (a: DataType, b: DataType) => Result): Result {
    if(a === undefined || b === undefined) {
        if(a === undefined && b !== undefined) {
            return -1;
        } else if(a !== undefined&& b === undefined) {
            return 1;
        }
        return 0;
    }

    if(a === null || b === null) {
        if(a === null && b !== null) {
            return -1;
        } else if(a !== null&& b === null) {
            return 1;
        }
        return 0;
    }

    if(a instanceof serialization.Serializable && b instanceof serialization.Serializable) {
        const comparator = new Comparator(a,b);
        a.marshal(comparator);
        return comparator.result;
    }

    if(comparator) return comparator(a,b);

    const use_native_comparator = ['string', 'number', 'boolean', 'object'];
    if(use_native_comparator.includes(typeof(a)) && use_native_comparator.includes(typeof(b))) {
        if(a < b) {
            return -1;
        } else if(a > b) {
            return 1;
        }
        return 0;
    }

    return undefined;
}
