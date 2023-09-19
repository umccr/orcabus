import { Client } from 'edgedb';
import { injectable, inject } from 'tsyringe';

@injectable()
export class LibraryLoaderService {
  constructor(@inject('Database') private readonly edgeDbClient: Client) {}

  public fetchAndLoad() {
    console.log('fetching');
  }
}
