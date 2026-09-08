// Cypress selectors. Measured defect: an unconstrained `$A.get($PATH, ...)` filed 124 of
// these as inbound routes on the estate it met after the one it was written on.
describe('account', () => {
  it('creates', () => {
    cy.get('#create-account-btn').click();
    cy.get('#username').type('a');
    cy.post('#nope');
  });
});

// Ordinary collection and map access, which is not a route and not a database.
const m = new Map();
m.get('k');
m.delete('k');
const found = [1, 2, 3].find(x => x > 1);
const made = [1, 2].map(x => x).filter(Boolean);
