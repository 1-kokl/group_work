"""Generate ordinary JMeter 5.6.3 plans; no external plugins are required."""
from pathlib import Path
from xml.etree import ElementTree as E
from common import ROOT


def prop(parent, name, value, kind="stringProp"):
    node = E.SubElement(parent, kind, name=name)
    node.text = str(value)
    return node


def component(tree, tag, gui, name, **attrs):
    node = E.SubElement(tree, tag, guiclass=gui, testclass=tag, testname=name, enabled="true", **attrs)
    return node, E.SubElement(tree, "hashTree")


def sampler(tree, label, method, path, body=None, token=False, expected=200, check="true"):
    http, children = component(tree, "HTTPSamplerProxy", "HttpTestSampleGui", label)
    args = E.SubElement(http, "elementProp", name="HTTPsampler.Arguments", elementType="Arguments")
    collection = E.SubElement(args, "collectionProp", name="Arguments.arguments")
    if body is not None:
        arg = E.SubElement(collection, "elementProp", name="", elementType="HTTPArgument")
        prop(arg, "HTTPArgument.always_encode", "false", "boolProp")
        prop(arg, "Argument.value", body)
        prop(arg, "Argument.metadata", "=")
        prop(http, "HTTPSampler.postBodyRaw", "true", "boolProp")
    for key, value in {
        "domain": "${__P(host,127.0.0.1)}", "port": "${__P(port,5099)}", "protocol": "http",
        "path": path, "method": method, "contentEncoding": "UTF-8",
        "connect_timeout": "10000", "response_timeout": "30000",
    }.items():
        prop(http, "HTTPSampler."+key, value)
    prop(http, "HTTPSampler.follow_redirects", "false", "boolProp")
    prop(http, "HTTPSampler.use_keepalive", "true", "boolProp")
    headers, _ = component(children, "HeaderManager", "HeaderPanel", "JSON headers")
    coll = E.SubElement(headers, "collectionProp", name="HeaderManager.headers")
    values = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        values["Authorization"] = "Bearer ${access_token}"
    for key, value in values.items():
        item = E.SubElement(coll, "elementProp", name=key, elementType="Header")
        prop(item, "Header.name", key)
        prop(item, "Header.value", value)
    assertion, _ = component(children, "JSR223Assertion", "TestBeanGUI", "HTTP and business success")
    prop(assertion, "scriptLanguage", "groovy")
    prop(assertion, "cacheKey", "true")
    prop(assertion, "script", f"""
try {{
    def body = new groovy.json.JsonSlurper().parseText(prev.getResponseDataAsString())
    if (prev.getResponseCode() != '{expected}' || body.code != {expected} || !({check})) {{
        AssertionResult.setFailure(true)
        AssertionResult.setFailureMessage('HTTP/business assertion failed')
    }}
}} catch (Exception ignored) {{
    AssertionResult.setFailure(true)
    AssertionResult.setFailureMessage('Response is not valid JSON')
}}
""".strip())
    return children


def build(scenario):
    root = E.Element("jmeterTestPlan", version="1.2", properties="5.0", jmeter="5.6.3")
    tree = E.SubElement(root, "hashTree")
    plan, plans = component(tree, "TestPlan", "TestPlanGui", "Week 9 "+scenario)
    prop(plan, "TestPlan.functional_mode", "false", "boolProp")
    variables = E.SubElement(plan, "elementProp", name="TestPlan.user_defined_variables", elementType="Arguments", guiclass="ArgumentsPanel", testclass="Arguments", testname="Variables", enabled="true")
    E.SubElement(variables, "collectionProp", name="Arguments.arguments")
    group, tests = component(plans, "ThreadGroup", "ThreadGroupGui", scenario)
    prop(group, "ThreadGroup.on_sample_error", "continue")
    controller = E.SubElement(group, "elementProp", name="ThreadGroup.main_controller", elementType="LoopController", guiclass="LoopControlPanel", testclass="LoopController", testname="Loop", enabled="true")
    prop(controller, "LoopController.continue_forever", "false", "boolProp")
    prop(controller, "LoopController.loops", "-1")
    prop(group, "ThreadGroup.num_threads", "${__P(threads,10)}")
    prop(group, "ThreadGroup.ramp_time", "${__P(ramp,2)}")
    prop(group, "ThreadGroup.scheduler", "true", "boolProp")
    prop(group, "ThreadGroup.duration", "${__P(duration,35)}")
    prop(group, "ThreadGroup.delay", "0")
    login_body = '{"username":"perf_${__threadNum}","password":"${__P(password,Week9-Local-Only!)}"}'
    if scenario == "login":
        sampler(tests, "login", "POST", "/api/v1/auth/login", login_body, check="body.data?.access_token")
    elif scenario == "products":
        sampler(tests, "products", "GET", "/api/ecommerce/products?page=1&per_page=20&category=category-03", check="body.data?.items?.size() == 20 && body.data.items.every { it.seller_username }")
    else:
        once, once_tree = component(tests, "OnceOnlyController", "OnceOnlyControllerGui", "Login once per virtual user")
        extraction_tree = sampler(once_tree, "setup_login", "POST", "/api/v1/auth/login", login_body, check="body.data?.access_token")
        extractor, _ = component(extraction_tree, "JSONPostProcessor", "JSONPostProcessorGui", "Extract access token")
        prop(extractor, "JSONPostProcessor.referenceNames", "access_token")
        prop(extractor, "JSONPostProcessor.jsonPathExprs", "$.data.access_token")
        prop(extractor, "JSONPostProcessor.match_numbers", "1")
        prop(extractor, "JSONPostProcessor.defaultValues", "MISSING_TOKEN")
        sampler(tests, "prepare_cart", "POST", "/api/ecommerce/cart", '{"product_id":"perf-product-${__threadNum}","quantity":1}', token=True)
        sampler(tests, "orders", "POST", "/api/ecommerce/orders", '{"shipping_address":"Synthetic local address","contact_phone":"13800000000"}', token=True, expected=201, check="body.data?.id && body.data?.items?.size() == 1 && body.data?.status == 'pending'")
    E.indent(root)
    output = ROOT / "performance" / "jmeter" / (scenario+".jmx")
    output.parent.mkdir(parents=True, exist_ok=True)
    E.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
    print(output)


if __name__ == "__main__":
    for name in ["login", "products", "orders"]:
        build(name)
