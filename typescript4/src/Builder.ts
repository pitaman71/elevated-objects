import { Serializable } from './Serializable';

export class Builder<T extends Serializable> {
    classSpec: string;
    allocator: (initializer?: any) => T;

    constructor(classSpec: string, allocator: (initializer?: any) => T) {
        this.classSpec = classSpec;
        this.allocator = allocator;
    }

    make(initializer?: any): T {
        return this.allocator(initializer);
    }
}
