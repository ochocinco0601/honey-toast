// A bean factory returning a builder. `WebClient.$M(...)` matches this and files a
// builder as an outbound call while missing the real calls.
const builder = WebClient.builder();

// Collections, forms and observables — the receivers an unconstrained `$R.get(...)` collects.
const params = new Map<string, string>();
params.get('id');
params.delete('id');
const form = new FormData();
form.get('field');
const items = [1, 2, 3];
items.find(x => x > 1);
const el = document.querySelector('#a');
const store = { create: (x: any) => x };
store.create({});

// Service method calls named like ORM calls: an unconstrained
// `$M.findAll(...)` files these as database reads.
class Consumer {
  constructor(private readonly articleService: any, private readonly tagService: any) {}
  async load() {
    await this.articleService.findAll({});
    await this.tagService.findAll();
    await this.articleService.findOne('slug');
  }
}
