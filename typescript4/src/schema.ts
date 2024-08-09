
export type Node<T> =
  T extends boolean ? "boolean" :
  T extends string ? "string" :
  T extends Function ? "function" :
  T extends number ? "number" :
  T extends bigint ? "bigint" :
  T extends symbol ? "symbol" :
  T extends any[] ? T[number] :
  {
    [K in keyof T]: Node<T[K]>
  };
