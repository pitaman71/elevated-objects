import { Serializable } from './serialization';
import { Factories, Factory } from './construction';
import { Visitor } from './traversal';

export class Reader<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    factories: Factories;
    factory: Factory<ExpectedType>;
    json: any;
    obj: ExpectedType|undefined;
    refs: { [key:string]: { [key:string]: any } };
    is_ref: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(
        factories: Factories,
        factory: Factory<ExpectedType>, 
        json: any, 
        refs?: { [key:string]: { [key:string]: any } }
    ) {
        this.factories = factories;
        this.factory = factory;
        this.json = json;
        this.refs = refs ? refs : {};
        this.is_ref = false;
    }

    getFactories(): Factories { return this.factories; }

    jsonPreview(): string {
        return(JSON.stringify(this.json).substr(0,80));
    }

    begin(obj: ExpectedType) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if(!this.obj) {
            this.obj = obj;
        }
        const className = this.factory.getClassSpec();
        if(!this.refs.hasOwnProperty(className)) {
            this.refs[className] = {};
        }
        const by_id = this.refs[className];
        if(this.json.hasOwnProperty('__id__')) {
            if(by_id.hasOwnProperty(this.json['__id__'])) {
                this.obj = <ExpectedType>by_id[this.json['__id__']];
                this.is_ref = true;
            } else {
                by_id[this.json['__id__']] = this.obj;
            }
        }
    }

    end(obj:ExpectedType) {
        //Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
    }

    owner(target: ExpectedType, ownerPropName: string): void {}

    verbatim<DataType>(
        target: Serializable, 
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>                
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        setValue(target, this.json);
    }    

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if(this.json === undefined) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {
            const newValue = (typeof(this.json[propName]) === 'string')  && fromString ? fromString(this.json[propName]) : this.json[propName];
            target[propName] = newValue;
        }
    }    

    scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)
        if(this.json === undefined) {
            target[propName] = undefined;
        } else if(this.json.hasOwnProperty(propName)) {            
            const item = this.json[propName];
            if(item === null) {
                target[propName] = null;
            } else {
                const reader = new Reader<ElementType>(this.factories, elementFactory, item, this.refs);
                reader.read();
                if(reader.obj) {
                    target[propName] = reader.obj;
                }
            }
        }
    }

    array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.json === undefined) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {     
            const propValue = this.json[propName];            
            const newValue = propValue.map((item: any) => {
                if(item === null) {
                    return null;
                } else {
                    const reader = new Reader<ElementType>(this.factories, elementFactory, item, this.refs);
                    reader.read();
                    return(reader.obj);
                }
            }).filter((item: ElementType|undefined): item is ElementType => !!item);
            target[propName] = newValue;
        }
    }

    map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.json === undefined) {
            throw new Error('No JSON here');
        } else if(this.json.hasOwnProperty(propName)) {     
            const propValue = this.json[propName];            
            const newValue = Object.getOwnPropertyNames(propValue).reduce((newValue: any, key: string) => {
                const item = propValue[key];
                if(item === null) {
                    return { ... newValue, [key]: null};
                } else {
                    const reader = new Reader<ElementType>(this.factories, elementFactory, item, this.refs);
                    reader.read();
                    return { ... newValue, [key]: reader.obj};
                }
            }, {});
            target[propName] = newValue;
        }
    }

    read(): any {
        const classSpec = 
            this.json && this.json.hasOwnProperty('__class__') ? this.json['__class__'] : this.factory.getClassSpec();

        if(this.json === undefined) {
            this.obj = undefined;
        } else {
            const newObject = this.factory.make();
            newObject.marshal(this);
            this.obj = <ExpectedType>newObject;
            return newObject;
        }
    }
}

export class Writer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    factories: Factories;
    factory: Factory<ExpectedType>;
    obj:ExpectedType;
    json: any;
    refs: { [key:string]: any[] };
    is_ref?: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(
        factories: Factories,
        factory: Factory<ExpectedType>, 
        obj: ExpectedType, 
        refs?: { [key:string]: object[] }
    ) {
        this.factories = factories;
        this.factory = factory;
        this.obj = obj;
        this.refs = refs ? refs : {};
    }

    getFactories(): Factories { return this.factories; }

    begin(obj: ExpectedType) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        this.json = {};
        
        const classSpec = this.factory.getClassSpec();
        if(!this.refs.hasOwnProperty(classSpec)) {
            this.refs[classSpec] = [];
        }
        this.json['__class__'] = classSpec;
        if(!classSpec) {
            throw new Error(`Cannot find class name for ${typeof obj}`);
        }
        let object_id = obj.getGlobalId();
        if(object_id !== null) {
            this.is_ref = this.refs[classSpec].includes(object_id);
        } else if(this.refs[classSpec].includes(obj)) {
            this.is_ref = true;
            object_id = this.refs[classSpec].indexOf(obj);
        } else {
            this.is_ref = false;
            object_id = this.refs[classSpec].length;
            this.refs[classSpec].push(obj);
        }
        this.json['__id__'] = object_id;
        this.json['__is_ref__'] = this.is_ref;
    }

    end(obj: ExpectedType) {
    }

    owner(target: ExpectedType, ownerPropName: string): void {}

    verbatim<DataType>(
        target: any, 
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void,
        getPropNames: () => Array<string>                
    ): void {
        this.json = getValue(target);
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        if(target[propName] !== undefined && !this.is_ref) {
            this.json[propName] = target[propName];
        }
    }

    scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if(this.is_ref) return;
        if(target.hasOwnPropertyName(propName)) {
            if(target[propName] === null) {
                this.json[propName] = null;
            } else {
                const writer = new Writer<ElementType>(this.factories, elementFactory, target[propName], this.refs);
                writer.write();
                this.json[propName] = writer.json;
            }
        }
    }

    array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.is_ref) return;

        if(target.hasOwnPropertyName(propName)) {
            this.json[propName] = target[propName].map((item: ElementType) => {
                if(item === null) {
                    return null;
                } else {
                    const writer = new Writer<ElementType>(this.factories, elementFactory, item, this.refs);
                    writer.write();
                    return writer.json;
                }
            }).filter((json:any) => !!json);
        }
    }

    map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        target: any, 
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if(this.is_ref) return;

        if(target.hasOwnPropertyName(propName)) {
            this.json[propName] = target[propName].reduce((newValue: any, item: ElementType) => {
                if(item === null) {
                    return { ... newValue, [propName]: null };
                } else {
                    const writer = new Writer<ElementType>(this.factories, elementFactory, item, this.refs);
                    writer.write();
                    return { ... newValue, [propName]: writer.json };
                }
            }, {});
        }
    }

    write(): any {
        if(!!this.json) {
            // pass
        } else if(this.obj instanceof Serializable) {
            this.obj.marshal(this);
        } else {
            this.json = this.obj;
        }
        return this.json;
    }
}

export function toJSON(factories: Factories, obj: any, path?: any[]): any {
    const usePath = path || [];
    if(obj instanceof Serializable) {
        const writer = new Writer<any>(factories, obj.__factory__, {});
        writer.write();
        return writer.json;
    } else if(Array.isArray(obj)) {
        const result = obj.map((item: any, index: number) => toJSON(factories, item, [ ...usePath, index]));
        return result;
    } else if(obj === Object(obj)) {
        const result = Object.getOwnPropertyNames(obj).reduce((result: any, propName: string) => {
            result[propName] = toJSON(factories, obj[propName], [ ...usePath, propName]);
            return result;
        }, {});
        return result;
    } else {
        return obj;
    }
}

export function fromJSON(factories: Factories, json: any): any {
    if(json && json.hasOwnProperty('__class__') && factories.hasClass(json['__class__'])) {
        const reader = new Reader<any>(factories, factories.getFactory(json['__class__']), json, {}); 
        reader.read();
        return reader.obj;
    } else if(Array.isArray(json)) {
        return json.map((item: any) => fromJSON(factories, item));
    } else if(json === Object(json)) {
        return Object.getOwnPropertyNames(json).reduce((result: any, propName: string) => {
            result[propName] = fromJSON(factories, json[propName]);
            return result;
        }, {});
    } else {
        return json;
    }
}

export function toString(factories: Factories, obj: any): string {
    return JSON.stringify(toJSON(factories, obj, []));
}

export function fromString(factories: Factories, text: string) {
    return fromJSON(factories, JSON.parse(text));
}
