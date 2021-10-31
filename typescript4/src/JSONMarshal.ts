import { Serializable } from './serialization';
import { factories, Factory } from './construction';
import { Visitor } from './traversal';
import * as CodeInstruments from 'code-instruments';
import { Reference } from './references';

export var logEnable = () => false;

export class Reader<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    factory: Factory<ExpectedType>;
    json: any;
    obj: ExpectedType|undefined;
    refs: { [className:string]: { [objectId:string]: Serializable } };
    is_ref: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(
        factory: Factory<ExpectedType>, 
        json: any, 
        refs?: { [key:string]: { [key:string]: Serializable } }
    ) {
        this.factory = factory;
        this.json = json;
        this.refs = refs ? refs : {};
        this.is_ref = false;
    }

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
        setValue: (target: Serializable, value: any) => void
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        new CodeInstruments.Task.Task('JSONMarshal.Reader.verbatim').logs(console.log, logEnable).returns({}, () => {
            setValue(target, this.json);
        });
    }    

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        new CodeInstruments.Task.Task(`JSONMarshal.Reader.primitive(${propName})`).logs(console.log, logEnable).returns({}, () => {
            if(this.json === undefined) {
                throw new Error('No JSON here');
            } else if(this.json.hasOwnProperty(propName)) {
                const newValue = (typeof(this.json[propName]) === 'string')  && fromString ? fromString(this.json[propName]) : this.json[propName];
                target[propName] = fromJSON(newValue);
            }
        });
    }    

    reference<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void {
        const target = <any>this.obj;
        const reader = new Reader<Reference<ElementType>>(Reference.Factory, this.json[propName]);        
        target[propName] = reader.read();
    }

    scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)
        new CodeInstruments.Task.Task(`JSONMarshal.Reader.primitive(${propName})`).logs(console.log, logEnable).returns({}, () => {
            const target = <any>this.obj;
            if(this.json === undefined) {
                target[propName] = undefined;
            } else if(this.json.hasOwnProperty(propName)) {            
                const item = this.json[propName];
                if(item === null) {
                    target[propName] = null;
                } else {
                    const reader = new Reader<ElementType>(elementFactory, item, this.refs);
                    reader.read();
                    if(reader.obj) {
                        target[propName] = reader.obj;
                    }
                }
            }
        });
    }

    array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        new CodeInstruments.Task.Task(`JSONMarshal.Reader.array(${propName})`).logs(console.log, logEnable).returns({}, () => {
            const target = <any>this.obj;
            if(this.json === undefined) {
                throw new Error('No JSON here');
            } else if(this.json.hasOwnProperty(propName)) {     
                const propValue = this.json[propName];            
                const newValue = propValue.map((item: any) => {
                    if(item === null) {
                        return null;
                    } else {
                        const reader = new Reader<ElementType>(elementFactory, item, this.refs);
                        reader.read();
                        return(reader.obj);
                    }
                }).filter((item: ElementType|undefined): item is ElementType => !!item);
                target[propName] = newValue;
            }
        });
    }

    map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        new CodeInstruments.Task.Task(`JSONMarshal.Reader.map(${propName})`).logs(console.log, logEnable).returns({}, () => {
            const target = <any>this.obj;
            if(this.json === undefined) {
                throw new Error('No JSON here');
            } else if(this.json.hasOwnProperty(propName)) {     
                const propValue = this.json[propName];            
                const newValue = Object.getOwnPropertyNames(propValue).reduce((newValue: any, key: string) => {
                    const item = propValue[key];
                    if(item === null) {
                        return { ... newValue, [key]: null};
                    } else {
                        const reader = new Reader<ElementType>(elementFactory, item, this.refs);
                        reader.read();
                        return { ... newValue, [key]: reader.obj};
                    }
                }, {});
                target[propName] = newValue;
            }
        });
    }

    read(): any {
        return new CodeInstruments.Task.Task(`JSONMarshal.Reader.read`).logs(console.log, logEnable).returns({}, () => {
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
        });
    }
}

export class Writer<ExpectedType extends Serializable> implements Visitor<ExpectedType> {
    factory: Factory<ExpectedType>;
    obj:ExpectedType;
    json: any;
    refs: { [className: string]: { [objectId: string] : Serializable} };
    is_ref?: boolean;

    // Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    constructor(
        factory: Factory<ExpectedType>, 
        obj: ExpectedType, 
        refs?: { [className: string]: { [objectId: string] : Serializable} }
    ) {
        this.factory = factory;
        this.obj = obj;
        this.refs = refs ? refs : {};
    }

    begin(obj: ExpectedType) {
        // Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        this.json = {};
        
        const classSpec = this.factory.getClassSpec();
        if(!this.refs.hasOwnProperty(classSpec)) {
            this.refs[classSpec] = {};
        }
        this.json['__class__'] = classSpec;
        if(!classSpec) {
            throw new Error(`Cannot find class name for ${typeof obj}`);
        }
        let object_id = obj.getGlobalId();
        if(object_id !== null) {
            this.is_ref = this.refs[classSpec].hasOwnProperty(object_id);
            this.json['__id__'] = object_id;
        } else {
            this.is_ref = false;
        }
        this.json['__is_ref__'] = this.is_ref;
    }

    end(obj: ExpectedType) {
    }

    owner(target: ExpectedType, ownerPropName: string): void {}

    verbatim<DataType>(
        target: Serializable,
        getValue: (target: Serializable) => any,
        setValue: (target: Serializable, value: any) => void
    ): void {
        new CodeInstruments.Task.Task(`JSONMarshal.Writer.verbatim`).logs(console.log, logEnable).returns({}, () => {
            this.json = getValue(target);
        });
    }

    primitive<PropType>(target: any, propName: string, fromString?: (initializer:string) => PropType): void {
        new CodeInstruments.Task.Task(`JSONMarshal.Writer.primitive(${propName})`).logs(console.log, logEnable).returns({}, () => {
            if(target[propName] !== undefined && !this.is_ref) {
                this.json[propName] = toJSON(target[propName]);
            }
        });
    }

    reference<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string
    ): void {
        const target = <any>this.obj;
        const writer = new Writer<Reference<ElementType>>(Reference.Factory, target[propName]);
        this.json[propName] = writer.write();
    }

    scalar<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        // Expect that the attribute value is probably not a reference to a shared object (though it may be)

        new CodeInstruments.Task.Task(`JSONMarshal.Writer.scalar(${propName})`).logs(console.log, logEnable).returns({}, () => {
            if(this.is_ref) return;
            const target = <any>this.obj;
            if(target.hasOwnProperty(propName)) {
                if(target[propName] === null) {
                    this.json[propName] = null;
                } else {
                    const writer = new Writer<ElementType>(elementFactory, target[propName], this.refs);
                    writer.write();
                    this.json[propName] = writer.json;
                }
            }
        });
    }

    array<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        new CodeInstruments.Task.Task(`JSONMarshal.Writer.array(${propName})`).logs(console.log, logEnable).returns({}, () => {
            if(this.is_ref) return;
            const target = <any>this.obj;
            if(target.hasOwnProperty(propName)) {
                this.json[propName] = target[propName].map((item: ElementType) => {
                    if(item === null) {
                        return null;
                    } else {
                        const writer = new Writer<ElementType>(elementFactory, item, this.refs);
                        writer.write();
                        return writer.json;
                    }
                }).filter((json:any) => !!json);
            }
        });
    }

    map<ElementType extends Serializable>(
        elementFactory: Factory<ElementType>,
        propName: string        
    ): void {
        // For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        // Expect that the attribute value is probably a reference to a shared object (though it may not be)

        new CodeInstruments.Task.Task(`JSONMarshal.Writer.map(${propName})`).logs(console.log, logEnable).returns({}, () => {
            if(this.is_ref) return;
            const target = <any>this.obj;
            if(target.hasOwnProperty(propName)) {
                this.json[propName] = target[propName].reduce((newValue: any, item: ElementType) => {
                    if(item === null) {
                        return { ... newValue, [propName]: null };
                    } else {
                        const writer = new Writer<ElementType>(elementFactory, item, this.refs);
                        writer.write();
                        return { ... newValue, [propName]: writer.json };
                    }
                }, {});
            }
        });
    }

    write(): any {
        return new CodeInstruments.Task.Task(`JSONMarshal.Writer.write`).logs(console.log, logEnable).returns({ obj: this.obj?.toString() }, () => {
            if(!!this.json) {
                // !! should probably be an error
            } else if(this.obj instanceof Serializable) {
                this.obj.marshal(this);
            } else {
                // handles this.obj === undefined, equivalent json is also undefined
                // handles this.obj === null, equivalent json is null
                this.json = this.obj;
            }
            return this.json;
        });
    }
}

export function toJSON(obj: any, path?: any[]): any {
    const usePath = path || [];
    if(obj instanceof Serializable) {
        const writer = new Writer<any>(obj.getFactory(), obj);
        writer.write();
        return writer.json;
    } else if(Array.isArray(obj)) {
        const result = obj.map((item: any, index: number) => toJSON(item, [ ...usePath, index]));
        return result;
    } else if(obj instanceof Set) {
        return { 
            '__native__': 'Set',
            '__values__': Array.from(obj).map((item: any, index: number) => toJSON(item, [ ...usePath, index]))
        };
    } else if(obj === Object(obj)) {
        const result = Object.getOwnPropertyNames(obj).reduce((result: any, propName: string) => {
            result[propName] = toJSON(obj[propName], [ ...usePath, propName]);
            return result;
        }, {});
        return result;
    } else {
        return obj;
    }
}

export function fromJSON(json: any): any {
    if(json && json.hasOwnProperty('__class__') && factories.hasClass(json['__class__'])) {
        const reader = new Reader<any>(factories.getFactory(json['__class__']), json, {}); 
        reader.read();
        return reader.obj;
    } else if(json && json.hasOwnProperty('__native__') && json['__native__'] === 'Set' && json.hasOwnProperty('__values__') ) {
            return new Set(fromJSON(json['__values__']));
        } else if(Array.isArray(json)) {
        return json.map((item: any) => fromJSON(item));
    } else if(json === Object(json)) {
        return Object.getOwnPropertyNames(json).reduce((result: any, propName: string) => {
            result[propName] = fromJSON(json[propName]);
            return result;
        }, {});
    } else {
        return json;
    }
}

export function toString(obj: any): string {
    return JSON.stringify(toJSON(obj, []));
}

export function fromString(text: string) {
    return fromJSON(JSON.parse(text));
}
