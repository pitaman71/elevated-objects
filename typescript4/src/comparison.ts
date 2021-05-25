import { Builder } from './construction';
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
        target: any, 
        propName: string,
        getValue: (target: ExpectedType) => any,
        setValue: (target: ExpectedType, value: any) => void,
        getPropNames: () => Array<string>        
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

    scalar<ElementType extends serialization.Serializable>(
        target: any, 
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
        } 
        this.result = cmp(aProp.id(), bProp.id());
        return this.result;
    }

    array<ElementType extends serialization.Serializable>(
        target: any, 
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

        const aProp = this.a[propName].map((propValue: ElementType) => propValue.id());
        const bProp = this.b[propName].map((propValue: ElementType) => propValue.id());
        this.result = cmp(aProp, bProp);
        return this.result;
    }

    map<ElementType extends serialization.Serializable>(
        target: any, 
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

        const aProp = Object.getOwnPropertyNames(this.a[propName]).reduce((ids: any, key: string) => this.a[propName][key].id());
        const bProp = Object.getOwnPropertyNames(this.b[propName]).reduce((ids: any, key: string) => this.b[propName][key].id());
        this.result = cmp(aProp, bProp);
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
