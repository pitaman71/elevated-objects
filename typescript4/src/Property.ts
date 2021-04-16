export interface Property<PropType> {
    value: PropType|undefined;
    setValue: (value: PropType) => void;
}

export class Primitive<ExpectedType> implements Property<ExpectedType> {
    propName: string;
    value: ExpectedType|undefined;
    setValue: (value: ExpectedType) => void;

    constructor(target: any, propName: string) {
        this.propName = propName;
        this.value = target[propName];
        this.setValue = (value: ExpectedType) => target[propName] = value;
    }
}

export class Scalar<ExpectedType> implements Property<ExpectedType> {
    propName: string;
    value: ExpectedType|undefined;
    setValue: (value: ExpectedType) => void;

    constructor(target: any, propName: string) {
        this.propName = propName;
        this.value = target[propName];
        this.setValue = (value: ExpectedType) => target[propName] = value;
    }
}

export class ArrayProp<ExpectedType> implements Property<ExpectedType[]> {
    propName: string;
    value: ExpectedType[]|undefined;
    setValue: (value: ExpectedType[]) => void;

    constructor(target: any, propName: string) {
        this.propName = propName;
        this.value = target[propName];
        this.setValue = (value: ExpectedType[]) => target[propName] = value;
    }
}

