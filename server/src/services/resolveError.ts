/** Ошибки валидации / бизнес-логики для POST resolve-choice (near / exact). */
export class ResolveError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string
  ) {
    super(message);
    this.name = "ResolveError";
  }
}
