from datetime import date, datetime, timedelta, time
from couchforms.models import XFormInstance
from custom.opm.opm_reports.constants import InvalidRow, CFU1_XMLNS
from custom.opm.opm_reports.tests.case_reports import OPMCaseReportTestBase, OPMCase, MockCaseRow, \
    offset_date


class ConditionFourTestMixin(object):
    """
    Shared test class for two conditions that have significant overlap
    """
    expected_window = None

    @property
    def valid_dod(self):
        return offset_date(self.report_date, -(self.expected_window - 1))

    def valid_form(self, received_on):
        return self.valid_form_function(received_on)

    def get_condition(self, row):
        return self.condition_getter(row)


class TestChildMeasles(OPMCaseReportTestBase, ConditionFourTestMixin):
    expected_window = 12

    def setUp(self):
        super(TestChildMeasles, self).setUp()
        self.valid_form_function = _valid_measles_form
        self.condition_getter = lambda row: row.child_received_measles_vaccine

    def test_not_in_window(self):
        for dod in (self.valid_dod - timedelta(days=1), self.valid_dod + timedelta(days=32)):
            case = OPMCase(
                forms=[],
                dod=dod,
            )
            row = MockCaseRow(case, self.report)
            self.assertEqual(None, row.child_received_measles_vaccine)

    def test_in_window_no_data(self):
        case = OPMCase(
            forms=[],
            dod=self.valid_dod
        )
        row = MockCaseRow(case, self.report)
        self.assertEqual(False, self.get_condition(row))

    def test_in_window_with_data(self):
        for month in range(self.expected_window - 2, self.expected_window + 1):
            form_date = datetime.combine(offset_date(self.valid_dod, month), time())
            case = OPMCase(
                forms=[self.valid_form(form_date)],
                dod=self.valid_dod,
            )
            row = MockCaseRow(case, self.report)
            self.assertEqual(True, self.get_condition(row))

    def test_one_month_extension_valid(self):
        form_date = offset_date(self.report_datetime, 1)
        case = OPMCase(
            forms=[self.valid_form(form_date)],
            dod=self.valid_dod,
        )
        row = MockCaseRow(case, self.report)
        self.assertEqual(True, self.get_condition(row))

    def test_two_month_extension_not_valid(self):
        form_date = offset_date(self.report_datetime, 2)
        case = OPMCase(
            forms=[self.valid_form(form_date)],
            dod=self.valid_dod,
        )
        row = MockCaseRow(case, self.report)
        self.assertEqual(False, self.get_condition(row))

    def test_before_window_not_valid(self):
        form_date = datetime.combine(offset_date(self.valid_dod, 9), time())
        case = OPMCase(
            forms=[self.valid_form(form_date)],
            dod=self.valid_dod,
        )
        row = MockCaseRow(case, self.report)
        self.assertEqual(False, self.get_condition(row))


def _valid_measles_form(received_on):
    return XFormInstance(
        form={
            'child1': {
                'child1_child_measlesvacc': '1',
            }
        },
        received_on=received_on,
        xmlns=CFU1_XMLNS,
    )

