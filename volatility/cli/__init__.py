import argparse
import sys
import logging

from volatility.cli import argparse_adapter
import volatility.framework
import volatility.plugins
from volatility.framework import interfaces, plugins, configuration, contexts

__author__ = 'mike'

logging.basicConfig(filename = 'example.log', level = logging.DEBUG)
logger = logging.getLogger("volatility")


class CommandLine(object):
    def __init__(self):
        pass

    def run(self):
        ver = volatility.framework.version()
        sys.stdout.write("Volatility Framework 3 (version " + "{0}.{1}.{2}".format(ver[0], ver[1], ver[2]) + ")\n")

        volatility.framework.require_version(3, 0, 0)

        # TODO: Get global config options
        plugins.import_plugins()

        # TODO: Choose a plugin
        plugin = volatility.plugins.windows.pslist.PsList
        context, req_mapping = self.collect_plugin_requirements(plugin)
        parser = argparse.ArgumentParser(prog = 'volatility',
                                         description = "An open-source memory forensics framework")
        argparse_adapter.adapt_config(context.config, parser)

        # Run the argparser
        parser.parse_args()

        # Generate the layers from the arguments
        for req in req_mapping:
            factory = req_mapping[req]
            req.value = factory(context)

        # Construct and run the plugin
        plugin(context).run()

    @staticmethod
    def construct_translation_layer_factory(name, requirement):
        """Create a factory that can provides requirements for the configuration
           The factory also populates the
        """
        factory = contexts.LayerFactory(name, requirement,
                                        [contexts.physical.PhysicalContextModifier,
                                         contexts.intel.IntelContextModifier,
                                         contexts.windows.WindowsContextModifier])
        return factory

    def collect_plugin_requirements(self, plugin):
        """Generates the requirements necessary for the plugin"""
        reqs = plugin.requirements()
        req_mapping = {}
        context = contexts.Context()

        for req in reqs:
            context.config.add_item(req, plugin.__name__)
            if isinstance(req, configuration.TranslationLayerRequirement):
                # Choose an appropriate LayerFactory (add layer to the req.name so we don't blat the requirement itself
                namespace = interfaces.configuration.namespace_join([plugin.__name__, req.name + "_layer"])
                factory = self.construct_translation_layer_factory(namespace, req)
                req_mapping[req] = factory
                for facreq in factory.requirements():
                    context.config.add_item(facreq, namespace = namespace)
            else:
                context.config.add_item(req, plugin.__name__)
        return context, req_mapping



def main():
    CommandLine().run()