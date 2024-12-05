describe('My First Test', () => {
  it('Visits the index page', () => {
    cy.visit('/')
    cy.contains('Welcome')
  })

  it('Tests the upload form button for job announcement', () => {
    cy.visit('/')
    cy.get('#jobFile').attachFile('example.pdf') // Ensure you have a file named 'example.pdf' in the cypress/fixtures folder
    cy.get('#uploadForm').submit()
    cy.get('#loading').should('be.visible')
    cy.wait(5000) // Adjust the wait time as needed
    cy.get('#loading').should('not.be.visible')
    cy.get('#NUM').should('not.be.empty')
  })
})