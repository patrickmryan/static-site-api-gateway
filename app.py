from monocdk import App
from static_high_side.static_high_side_stack import StaticHighSideStack


app = App()
StaticHighSideStack(app, "static-high-side-site")

app.synth()
