# Copyright (C) 2019 Red Hat, Inc.

# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

from sos.plugins import Plugin, IndependentPlugin


class Istio(Plugin, IndependentPlugin):
    """Istio Service Mesh configuration
    """

    requires_root = False

    option_list = [
        ("kubeconfig", "specify the kubeconfig file to use with oc", "fast", ""),
        ("istio-ns", "specify the namespace Istio is installed", "fast", "istio-system")
    ]

    oc = "oc"
    istioctl = "istioctl"

    def setup(self):
        self._check_programs()

        if self.get_option("kubeconfig"):
            self.oc = "%s --kubeconfig=%s" % (self.oc,
                                             self.get_option("kubeconfig"))
        oc_get_cmd = '%s get' % self.oc
        oc_gety_cmd = '%s -o yaml' % oc_get_cmd

        oc_istio_cmd = "%s -n %s" % (self.oc, self.get_option("istio-ns"))
        oc_istio_get_cmd = "%s get" % (oc_istio_cmd)
        oc_istio_gety_cmd = "%s -o yaml" % (oc_istio_get_cmd)

        # Global stuff
        self.add_cmd_output('%s version' % (self.oc), 'oc_version')
        self.add_cmd_output('%s namespaces' % (oc_get_cmd), 'namespaces')
        self.add_cmd_output('%s crd' % (oc_get_cmd), 'crd')
        self.add_cmd_output('istioctl version --remote', 'istioctl_version')

        # Istio resources
        resources = [
            'deployments',
            'services',
            'pods',
            'replicasets',
            'hpa',
            'jobs',
            'routes',
            'configmaps',
            'MutatingWebhookConfiguration'
        ]

        for res in resources:
            self.add_cmd_output(cmds='%s %s' % (oc_istio_get_cmd, res),
                                suggest_filename=res)
            self.add_cmd_output(cmds='%s %s' % (oc_istio_gety_cmd, res),
                                suggest_filename='%s_full.yaml' % res)

        self.add_cmd_output('%s istio-io --all-namespaces' % oc_get_cmd, 'istio-io')
        self.add_cmd_output('%s istio-io --all-namespaces' % oc_gety_cmd, 'istio-io_full.yaml')

        # Images versions
        self.add_cmd_output(
            cmds='%s pods -o=jsonpath=\'{"Pods and Images\\n"}{"===============\\n"}{range .items[*]}{.metadata.labels.app} => {.spec.containers..image}{"\\n"}{end}\'' % (
                oc_istio_get_cmd),
            suggest_filename='image_versions'
        )

        # Logs
        if self.get_option("all_logs"):
            out = self.get_command_output('%s pods' % oc_istio_get_cmd)
            pods = [n.split()[0] for n in out['output'].splitlines()[1:] if n]
            for pod in pods:
                self.add_cmd_output('%s logs --all-containers %s' % (oc_istio_cmd, pod), 'logs_%s.log' % (pod))

    def _check_programs(self):
        if not self.check_ext_prog(self.oc):
            self.add_alert('Command %s not found' % self.oc)

        if not self.check_ext_prog(self.istioctl):
            self.add_alert('Command %s not found' % self.istioctl)

# vim: set et ts=4 sw=4 :
