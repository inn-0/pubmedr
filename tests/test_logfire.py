import logfire

from pubmedr import config

print(type(config))
logfire.configure()
logfire.info("Hello, {name}!", name="world")
