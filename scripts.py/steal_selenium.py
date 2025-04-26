
""" from selenium import webdriver

const builder = new Builder()
      .forBrowser("chrome")
      .usingServer(
        `http://0.0.0.0:3000/selenium`
      );

const driver = await builder.build();

console.log("Navigating to Google");
await driver.get("https://www.google.com"); """