import { Serializable } from './serialization';

type Allocator<ExpectedType extends Serializable> = (factory: Factory<ExpectedType>, initializer?: any) => ExpectedType;

export class Directory<ExpectedType> {
    classSpec: string;
    instances: Map<string|number, ExpectedType>;

    constructor(classSpec: string) {
        this.classSpec = classSpec;
        this.instances = new Map();
    }

    resolve(id: string, sample: ExpectedType): ExpectedType {
        if(id === null) return sample;
        const instance = this.instances.get(id);
        if(instance) return instance;
        this.instances.set(id, sample);
        return sample;
    }

    find(id: string): ExpectedType {
        const instance = this.instances.get(id);
        if(!instance) {
            throw new Error(`Unable to locate instance ${this.classSpec}"${id}"`)
        }
        return instance;
    }
}

export class Factory<ExpectedType extends Serializable> {
    classSpec: string;
    allocators: Map<string, Allocator<ExpectedType>>;

    static abstract<ExpectedType extends Serializable>(classSpec: string) {
        const result = new Factory<ExpectedType>(classSpec);
        return result;
    }

    static concrete<ExpectedType extends Serializable>(classSpec: string, 
        allocator: Allocator<ExpectedType>
    ) {
        const result = new Factory<ExpectedType>(classSpec);
        result.allocators.set(classSpec, allocator);
        return result;
    }

    static derived<ExpectedType extends Serializable>(classSpec: string, 
        allocator: Allocator<ExpectedType>,
        parentFactories: Factory<any>[]
    ) {
        const result = new Factory<ExpectedType>(classSpec);
        result.allocators.set(classSpec, allocator);
        parentFactories.forEach((parentFactory: Factory<any>) => {
            parentFactory.allocators = { 
                ... parentFactory.allocators,
                ... result.allocators
            };
        });
        return result;
    }

    constructor(classSpec: string) {
        this.classSpec = classSpec;
        this.allocators = new Map();
    }

    getClassSpec() {
        return this.classSpec;
    }

    make(classSpec?: string): ExpectedType {
        if(classSpec === undefined) {
            classSpec = this.classSpec;
        }

        if(!this.allocators.has(classSpec)) {
            throw new Error(`Object of type ${classSpec} cannot be instantiated with allocators ${Array.from(this.allocators.keys()).join(',')}`);
        }
        const allocator = this.allocators.get(classSpec);
        if(allocator === undefined) {
            throw new Error(`Factory is unable to find allocator function for ${classSpec}`)
        }
        const result = allocator(this);
        result.getFactory = () => this;
        return result
    }
}

export class Factories {
    specToBuilder: { [key: string]: Factory<Serializable> };

    constructor() {
        this.specToBuilder = {};
    }
    
    register<ExpectedType extends Serializable>(classSpec: string, factoryMaker: () => Factory<Serializable>): Factory<ExpectedType> {
        if(!Object.getOwnPropertyNames(this.specToBuilder).includes(classSpec)) {
            this.specToBuilder[classSpec] = factoryMaker();
        }
        const factory: any = this.specToBuilder[classSpec];
        return factory;
    }

    concrete<ExpectedType extends Serializable>(classSpec: string, objectMaker: () => ExpectedType): Factory<ExpectedType> {
        return this.register(classSpec, () => Factory.concrete<Serializable>(classSpec, objectMaker));
    }

    hasClass(classSpec?: string): boolean {
        return !!classSpec && this.specToBuilder.hasOwnProperty(classSpec);
    }

    getFactory(classSpec: string): Factory<any> {
        return this.specToBuilder[classSpec];
    }

    make(classSpec: string): Serializable {
        return this.specToBuilder[classSpec.toString()].make();
    }

    makeObjectId(): string {
        const length = 16;
        const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        const charactersLength = characters.length;
        let result = '';
        for ( let i = 0; i < length; i++ ) {
            result += characters.charAt(Math.floor(Math.random() * 
     charactersLength));
        }
        return result;
    }
}

export const factories = new Factories();

export class Builder<ExpectedType extends Serializable, DoneType> {
    factory: Factory<ExpectedType>;
    whenDone: (initializer?: any) => DoneType;
    built: ExpectedType;

    constructor(
        factory: Factory<ExpectedType>,
        whenDone: (initializer?: any) => DoneType = (x) => x,
        built?: ExpectedType
    ) {
        this.factory = factory;
        this.whenDone = whenDone;
        this.built = built || factory.make();
    }

    getClassSpec() { return this.factory.classSpec; }

    done(finisher: (built: ExpectedType) => ExpectedType = (x) => x): DoneType {
        return this.whenDone(finisher(this.built));
    }
}
