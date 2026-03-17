import '@testing-library/cypress/add-commands';

beforeEach(() => {
  cy.viewport(Cypress.config('viewportWidth'), Cypress.config('viewportHeight'));
});

