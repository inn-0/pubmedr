from pubmedr import config
import logfire

print(type(config))
logfire.configure()
logfire.info("Hello, {name}!", name="world")
