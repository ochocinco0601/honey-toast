// A bean factory returning a builder. Measured defect: `WebClient.$M(...)` matched this and
// produced every outbound fact in a run, all of them wrong, while the real calls were missed.
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

// Service method calls named like ORM calls. Measured defect: an unconstrained
// `$M.findAll(...)` filed three of these as database reads on the estate it was added against.
class Consumer {
  constructor(private readonly articleService: any, private readonly tagService: any) {}
  async load() {
    await this.articleService.findAll({});
    await this.tagService.findAll();
    await this.articleService.findOne('slug');
  }
}
