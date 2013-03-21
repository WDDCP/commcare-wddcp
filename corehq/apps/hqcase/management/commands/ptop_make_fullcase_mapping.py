from datetime import datetime
import hashlib
from django.core.management.base import NoArgsCommand
import sys
import os
from casexml.apps.case.models import CommCareCase
from corehq.apps.hqcase.management.commands.ptop_generate_mapping import MappingOutputCommand
from corehq.pillows import dynamic
from corehq.pillows.dynamic import DEFAULT_MAPPING_WRAPPER, case_special_types
from django.conf import settings
from corehq.pillows.fullcase import FullCasePillow

class Command(MappingOutputCommand):
    help="Generate mapping JSON of our ES indexed types. For casexml"
    option_list = NoArgsCommand.option_list + (
    )
    doc_class_str = "casexml.apps.case.models.CommCareCase"
    doc_class = CommCareCase


    def finish_handle(self):
        """
        Yes, this looks eerily similar to ptop_make_case_mapping
        Only thing flipping is dynamic=False to True on the top level mapping dict

        However, this FullCaseIndex is likely going to be a stopgap measure until we get
        a concept dictionary setup, so a little ugliness in execution will get things done for now
        """

        filepath = os.path.join(settings.FILEPATH, 'submodules','core-hq-src','corehq','pillows','mappings','fullcase_mapping.py')
        casepillow = FullCasePillow(create_index=False)

        #current index
        #check current index
        aliased_indices = casepillow.check_alias()

#        current_index = '%s_%s' % (casepillow.es_index_prefix, casepillow.calc_meta())
        current_index = casepillow.es_index

        #regenerate the mapping dict
        m = DEFAULT_MAPPING_WRAPPER
        m['dynamic'] = True

        m['properties'] = dynamic.set_properties(self.doc_class, custom_types=case_special_types)
        m['_meta']['comment'] = "Autogenerated [%s] mapping from ptop_generate_mapping %s" % (self.doc_class_str, datetime.utcnow().strftime('%m/%d/%Y'))
        casepillow.default_mapping = m
        delattr(casepillow, '_calc_meta_cache')
        output = []
        output.append('FULL_CASE_INDEX="%s_%s"' % (casepillow.es_index_prefix, casepillow.calc_meta()))
        output.append('FULL_CASE_MAPPING=%s' % m)
        newcalc_index = "%s_%s" % (casepillow.es_index_prefix, casepillow.calc_meta())
        print "Writing new case_index and mapping: %s" % output[0]
        with open(filepath, 'w') as outfile:
            outfile.write('\n'.join(output))

        if newcalc_index not in aliased_indices and newcalc_index != current_index:
            sys.stderr.write("\n\tWarning, current index %s is not aliased at the moment\n" % current_index)
            sys.stderr.write("\tCurrent live aliased index: %s\n\n"  % (','.join(aliased_indices)))

        sys.stderr.write("File written to %s\n" % filepath)



