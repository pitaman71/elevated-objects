// Core measurement dimensions
export type DimensionCategory = 
  'time' | 
  'length' | 
  'mass' | 
  'temperature' | 
  'electric_current' | 
  'luminous_intensity' | 
  'amount' |
  'angle' |
  'data' |
  'currency' |
  'frequency' |
  'force' |
  'pressure' |
  'energy' |
  'power' |
  'area' |
  'volume' |
  'velocity' |
  'acceleration';

// Time units
export type TimeUnits = 
  'nanosecond' | 'ns' |
  'microsecond' | 'μs' |
  'millisecond' | 'ms' |
  'second' | 's' |
  'minute' | 'min' |
  'hour' | 'h' |
  'day' | 'd' |
  'week' | 'wk' |
  'month' | 'mo' |
  'quarter' | 'q' |
  'year' | 'yr' |
  'decade' | 'dec' |
  'century' | 'cent';

// Length units
export type LengthUnits = 
  'nanometer' | 'nm' |
  'micrometer' | 'μm' |
  'millimeter' | 'mm' |
  'centimeter' | 'cm' |
  'inch' | 'in' |
  'foot' | 'ft' |
  'yard' | 'yd' |
  'meter' | 'm' |
  'kilometer' | 'km' |
  'mile' | 'mi' |
  'nautical_mile' | 'nmi' |
  'lightyear' | 'ly' |
  'astronomical_unit' | 'au' |
  'parsec' | 'pc';

// Mass units
export type MassUnits = 
  'microgram' | 'μg' |
  'milligram' | 'mg' |
  'gram' | 'g' |
  'kilogram' | 'kg' |
  'metric_ton' | 't' |
  'ounce' | 'oz' |
  'pound' | 'lb' |
  'stone' | 'st' |
  'short_ton' | 'ton' |
  'long_ton' | 'long_ton';

// Temperature units
export type TemperatureUnits = 
  'kelvin' | 'K' |
  'celsius' | 'C' | '°C' |
  'fahrenheit' | 'F' | '°F';

// Electric current units
export type ElectricCurrentUnits = 
  'ampere' | 'A' |
  'milliampere' | 'mA' |
  'microampere' | 'μA';

// Luminous intensity units
export type LuminousIntensityUnits = 
  'candela' | 'cd' |
  'lumen' | 'lm' |
  'lux' | 'lx';

// Amount units
export type AmountUnits = 
  'mole' | 'mol' |
  'millimole' | 'mmol' |
  'micromole' | 'μmol';

// Angle units
export type AngleUnits = 
  'degree' | '°' | 'deg' |
  'radian' | 'rad' |
  'gradian' | 'grad' |
  'arcminute' | 'arcmin' |
  'arcsecond' | 'arcsec';

// Data units
export type DataUnits = 
  'bit' | 'b' |
  'byte' | 'B' |
  'kilobyte' | 'KB' |
  'megabyte' | 'MB' |
  'gigabyte' | 'GB' |
  'terabyte' | 'TB' |
  'petabyte' | 'PB';

// Currency units (common ones)
export type CurrencyUnits = 
  'USD' | '$' |
  'EUR' | '€' |
  'GBP' | '£' |
  'JPY' | '¥' |
  'CNY' | '元' |
  'INR' | '₹' |
  'BTC' | '₿' |
  'ETH';

// Frequency units
export type FrequencyUnits = 
  'hertz' | 'Hz' |
  'kilohertz' | 'kHz' |
  'megahertz' | 'MHz' |
  'gigahertz' | 'GHz';

// Force units
export type ForceUnits = 
  'newton' | 'N' |
  'pound-force' | 'lbf' |
  'kilogram-force' | 'kgf' |
  'dyne' | 'dyn';

// Pressure units
export type PressureUnits = 
  'pascal' | 'Pa' |
  'kilopascal' | 'kPa' |
  'megapascal' | 'MPa' |
  'bar' | 'bar' |
  'atmosphere' | 'atm' |
  'millimeter_mercury' | 'mmHg' |
  'pounds_per_square_inch' | 'psi';

// Energy units
export type EnergyUnits = 
  'joule' | 'J' |
  'kilojoule' | 'kJ' |
  'calorie' | 'cal' |
  'kilocalorie' | 'kcal' |
  'watt_hour' | 'Wh' |
  'kilowatt_hour' | 'kWh' |
  'electronvolt' | 'eV' |
  'british_thermal_unit' | 'BTU';

// Power units
export type PowerUnits = 
  'watt' | 'W' |
  'kilowatt' | 'kW' |
  'megawatt' | 'MW' |
  'horsepower' | 'hp';

// Area units
export type AreaUnits = 
  'square_meter' | 'm²' |
  'square_kilometer' | 'km²' |
  'square_foot' | 'ft²' |
  'square_mile' | 'mi²' |
  'acre' | 'ac' |
  'hectare' | 'ha';

// Volume units
export type VolumeUnits = 
  'cubic_meter' | 'm³' |
  'liter' | 'L' |
  'milliliter' | 'mL' |
  'cubic_foot' | 'ft³' |
  'cubic_inch' | 'in³' |
  'US_gallon' | 'gal' |
  'US_fluid_ounce' | 'fl_oz' |
  'imperial_gallon' | 'imp_gal';

// Velocity units
export type VelocityUnits = 
  'meter_per_second' | 'm/s' |
  'kilometer_per_hour' | 'km/h' |
  'miles_per_hour' | 'mph' |
  'knot' | 'kn';

// Acceleration units
export type AccelerationUnits = 
  'meter_per_second_squared' | 'm/s²' |
  'foot_per_second_squared' | 'ft/s²' |
  'standard_gravity' | 'g';

// Union of all unit types
export type UnitType = 
  TimeUnits | 
  LengthUnits | 
  MassUnits | 
  TemperatureUnits | 
  ElectricCurrentUnits | 
  LuminousIntensityUnits | 
  AmountUnits | 
  AngleUnits | 
  DataUnits | 
  CurrencyUnits | 
  FrequencyUnits | 
  ForceUnits | 
  PressureUnits | 
  EnergyUnits | 
  PowerUnits | 
  AreaUnits | 
  VolumeUnits | 
  VelocityUnits | 
  AccelerationUnits;

// Common dimensions used in various fields
export type Dimension = {
  category: DimensionCategory;
  name: string;
  baseUnit: UnitType;
  description?: string;
};

// Mapping from dimension category to appropriate unit types
export interface DimensionUnitMap {
  time: TimeUnits;
  length: LengthUnits;
  mass: MassUnits;
  temperature: TemperatureUnits;
  electric_current: ElectricCurrentUnits;
  luminous_intensity: LuminousIntensityUnits;
  amount: AmountUnits;
  angle: AngleUnits;
  data: DataUnits;
  currency: CurrencyUnits;
  frequency: FrequencyUnits;
  force: ForceUnits;
  pressure: PressureUnits;
  energy: EnergyUnits;
  power: PowerUnits;
  area: AreaUnits;
  volume: VolumeUnits;
  velocity: VelocityUnits;
  acceleration: AccelerationUnits;
}

// Common dimensions used across different domains
export const COMMON_DIMENSIONS: Record<string, Dimension> = {
  // Time dimensions
  timeSinceMidnight: { 
    category: 'time', 
    name: 'timeSinceMidnight', 
    baseUnit: 'second',
    description: 'Time elapsed since midnight (00:00:00)'
  },
  age: { 
    category: 'time', 
    name: 'age', 
    baseUnit: 'year',
    description: 'Age of entity in years'
  },
  duration: { 
    category: 'time', 
    name: 'duration', 
    baseUnit: 'second',
    description: 'Duration of an event or process'
  },
  
  // Financial dimensions
  price: { 
    category: 'currency', 
    name: 'price', 
    baseUnit: 'USD',
    description: 'Monetary value of an item'
  },
  exchangeRate: { 
    category: 'currency', 
    name: 'exchangeRate', 
    baseUnit: 'USD',
    description: 'Exchange rate between currencies'
  },
  
  // Scientific dimensions
  temperature: { 
    category: 'temperature', 
    name: 'temperature', 
    baseUnit: 'kelvin',
    description: 'Measure of heat energy'
  },
  distance: { 
    category: 'length', 
    name: 'distance', 
    baseUnit: 'meter',
    description: 'Spatial separation between points'
  },
  mass: { 
    category: 'mass', 
    name: 'mass', 
    baseUnit: 'kilogram',
    description: 'Amount of matter'
  },
  
  // Engineering dimensions
  voltage: { 
    category: 'electric_current', 
    name: 'voltage', 
    baseUnit: 'ampere',
    description: 'Electric potential difference'
  },
  frequency: { 
    category: 'frequency', 
    name: 'frequency', 
    baseUnit: 'hertz',
    description: 'Number of cycles per time unit'
  }
};

// Measurement value with unit
export interface Measurement<T extends UnitType> {
  value: number;
  unit: T;
  dimension?: string;
}

// Conversion utility type
export interface UnitConverter<T extends UnitType> {
  convert: (measurement: Measurement<T>, targetUnit: T) => Measurement<T>;
  add: (a: Measurement<T>, b: Measurement<T>) => Measurement<T>;
  subtract: (a: Measurement<T>, b: Measurement<T>) => Measurement<T>;
  multiply: (measurement: Measurement<T>, factor: number) => Measurement<T>;
  divide: (measurement: Measurement<T>, divisor: number) => Measurement<T>;
  compare: (a: Measurement<T>, b: Measurement<T>) => number;
}

// Unit prefixes for metric system
export enum MetricPrefix {
  NANO = 1e-9,
  MICRO = 1e-6,
  MILLI = 1e-3,
  CENTI = 1e-2,
  DECI = 1e-1,
  BASE = 1,
  DECA = 1e1,
  HECTO = 1e2,
  KILO = 1e3,
  MEGA = 1e6,
  GIGA = 1e9,
  TERA = 1e12,
  PETA = 1e15
}