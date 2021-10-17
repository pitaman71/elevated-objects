import { Factory } from './construction';
import * as serialization from './serialization';
import * as traversal from './traversal';

enum Result {
    Unknown = 0,
    Less = -1,
    Equal = 0,
    Greater = 1
}

class Comparator<ExpectedType extends serialization.Serializable> implements traversal.Visitor<ExpectedType> {
    a: any;
    b: any;
    result: Result;

    constructor(a: ExpectedType, b: ExpectedType) {
        this.a = a;
        this.b = b;
        this.result = Result.Unknown;
    }

    begin(obj: ExpectedType, parentPropName?: string): Result {
        this.result = Result.Equal;
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
        if(this.result !== Result.Equal) {
            return this.result;
        }
        
        const aProp = getValue(this.a);
        const bProp = getValue(this.b);
        if(aProp === undefined && bProp !== undefined) {
            this.result = Result.Less;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = Result.Greater;
        } else if(aProp === undefined && bProp === undefined) {
            // pass
        } else if(aProp < bProp) {
            this.result = Result.Less;
        } else if(aProp > bProp) {
            this.result = Result.Greater;
        }
        return this.result;
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): Result {
        if(this.result !== Result.Equal) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = Result.Less;
        } else if(aHasProp && !bHasProp) {
            this.result = Result.Greater;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp === undefined && bProp !== undefined) {
            this.result = Result.Less;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = Result.Greater;
        } else if(aProp === undefined && bProp === undefined) {
            // pass
        } else if(aProp < bProp) {
            this.result = Result.Less;
        } else if(aProp > bProp) {
            this.result = Result.Greater;
        }
        return this.result;
    }

    reference<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        if(this.result !== Result.Equal) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = Result.Less;
        } else if(aHasProp && !bHasProp) {
            this.result = Result.Greater;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp._ref < bProp._ref) {
            this.result = Result.Less;
        } else if(aProp._ref > bProp._ref) {
            this.result = Result.Greater;
        } else if(aProp._def < bProp._def) {
            this.result = Result.Less;
        } else if(aProp._def > bProp._def) {
            this.result = Result.Greater;
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
            if(sub.result !== Result.Equal) {
                this.result = sub.result;
            }
        } else if(a_prop.getGlobalId() === null && b_prop.getGlobalId() !== null) {
            this.result = Result.Less;
        } else if(a_prop.getGlobalId() !== null && b_prop.getGlobalId() === null) {
            this.result = Result.Greater;
        } else if((a_prop.getGlobalId() || 0) < (b_prop.getGlobalId() || 0)) {
            this.result = Result.Less;
        } else if((a_prop.getGlobalId() || 0) >(b_prop.getGlobalId() || 0)) {
            this.result = Result.Less;
        }
    }

    scalar<ElementType extends serialization.Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): Result {
        if(this.result !== Result.Equal) {
            return this.result;
        }

        const aHasProp = this.a.hasOwnProperty(propName);
        const bHasProp = this.b.hasOwnProperty(propName);
        if(!aHasProp && !bHasProp) {
            return this.result;
        } else if(!aHasProp && bHasProp) {
            this.result = Result.Less;
        } else if(aHasProp && !bHasProp) {
            this.result = Result.Greater;
        }

        const aProp = this.a[propName];
        const bProp = this.b[propName];
        if(aProp === undefined && bProp === undefined) {
            return this.result;
        } else if(aProp === undefined && bProp !== undefined) {
            this.result = Result.Less;
        } else if(aProp !== undefined && bProp === undefined) {
            this.result = Result.Greater;
        } else {
            this.compare_elements(aProp, bProp);
        }
        if(this.result === Result.Unknown) {
            this.result = Result.Equal;
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
            this.result = Result.Less;
        } else if(aHasProp && !bHasProp) {
            this.result = Result.Greater;
        }
        if(this.a.length < this.b.length) {
            this.result = Result.Less;
        } else if(this.a.length > this.b.length) {
            this.result = Result.Greater;
        }

        this.a[propName].forEach((aProp: serialization.Serializable, index: number) => {
            const bProp = this.b[propName][index];
            if(this.result === Result.Unknown) {
                this.compare_elements(aProp, bProp);
            }
        });
        if(this.result === Result.Unknown) {
            this.result = Result.Equal;
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
            this.result = Result.Less;
        } else if(aHasProp && !bHasProp) {
            this.result = Result.Greater;
        }
        const aKeys = Object.getOwnPropertyNames(this.a[propName]);
        const bKeys = Object.getOwnPropertyNames(this.b[propName]);
        if(aKeys < bKeys) {
            this.result = Result.Less;
        } else if(aKeys > bKeys) {
            this.result = Result.Greater;
        }
        aKeys.forEach((key: string) => {
            if(this.result === Result.Unknown) {
                this.compare_elements(this.a[propName][key], this.b[propName][key]);
            }
        });
        if(this.result === Result.Unknown) {
            this.result = Result.Equal;
        }
        return this.result;
    }
}

export function cmp(a: any, b:any): Result {
    if(a === undefined && b === undefined) {
        return Result.Equal;
    } else if(a === undefined && b !== undefined) {
        return Result.Less;
    } else if(a !== undefined&& b === undefined) {
        return Result.Greater;
    }

    if(a === null && b === null) {
        return Result.Equal;
    } else if(a === null && b !== null) {
        return Result.Less;
    } else if(a !== null&& b === null) {
        return Result.Greater;
    }

    if(a instanceof serialization.Serializable && b instanceof serialization.Serializable) {
        const comparator = new Comparator(a,b);
        a.marshal(comparator);
        return comparator.result;
    }

    const use_native_comparator = ['string', 'number', 'boolean', 'object'];
    if(use_native_comparator.includes(typeof(a)) && use_native_comparator.includes(typeof(b))) {
        if(a < b) {
            return Result.Less;
        } else if(a > b) {
            return Result.Greater;
        }
        return Result.Equal;
    }

    return Result.Unknown;
}
