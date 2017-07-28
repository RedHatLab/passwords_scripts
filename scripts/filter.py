from abc import ABCMeta, abstractmethod
from prettytable import PrettyTable

import scripts.errorPrinter as errorPrinter


class FilterTemplate():

    __metaclass__ = ABCMeta

    def __init__(self, variable=None):
        if (variable):
            self.variable = variable

    def apply_check(self, data):
        if (not data):
            errorPrinter.printWarning(
                self.__class__.__name__,
                'No input data to be filtered'
            )
            return []

        return self.apply(data)

    @abstractmethod
    def apply(self, data):
        pass


class LowEntropyChange(FilterTemplate):

    def apply(self, data):
        low_entropychange_data = list(filter(
            lambda passdata: hasattr(passdata, 'orig_pass') and
            passdata.getEntropyChange() <= self.variable,
            data
        ))

        return low_entropychange_data


class PCLOutputChangedFromOk2NotOk(FilterTemplate):

    def apply(self, data):
        filtered_data = []
        for passdata in data:
            if (hasattr(passdata, 'transform_rules')):
                # Check only one PCL or check it for all PCLs
                pcl_list = self.variable if (hasattr(self, 'variable')) \
                    else passdata.pcl_output.keys()

                for pcl in pcl_list:
                    if (passdata.orig_pass.getPCLOutput(pcl) == "OK" and
                       passdata.getPCLOutput(pcl) != "OK"):
                        filtered_data.append(passdata)
                        break

        return filtered_data


class PCLOutputChangedFromNotOk2Ok(FilterTemplate):

    def apply(self, data):
        filtered_data = []
        for passdata in data:
            if (hasattr(passdata, 'transform_rules')):
                # Check only one PCL or check it for all PCLs
                pcl_list = self.variable if (hasattr(self, 'variable')) \
                    else passdata.pcl_output.keys()

                for pcl in pcl_list:
                    if (passdata.orig_pass.getPCLOutput(pcl) != "OK" and
                       passdata.getPCLOutput(pcl) == "OK"):
                        filtered_data.append(passdata)
                        break

        return filtered_data


class PCLOutputsAreNotAllSame(FilterTemplate):

    def apply(self, data):
        filtered_data = []

        pcl_list = data[0].pcl_output.keys()
        for passdata in data:
            counterOk = 0
            counterNotOk = 0
            for pcl in pcl_list:
                if (passdata.getPCLOutput(pcl) == "OK"):
                    counterOk += 1
                else:
                    counterNotOk += 1
            if (counterOk != len(pcl_list) and counterNotOk != len(pcl_list)):
                filtered_data.append(passdata)

        return filtered_data


class TransformationHadEffect(FilterTemplate):

    def check_transformation(self, passdata):
        for transformation in passdata.transform_rules:
            for input_transformation in self.variable:
                if (input_transformation in transformation):
                    if (transformation[input_transformation] != 0):
                        return passdata

        return None

    def apply(self, data):
        filtered_data = []
        if (not hasattr(self, 'variable')):
            errorPrinter.printWarning(
                self.__class__.__name__,
                'Set list of names of transformation as the' +
                'first argument in constructor.'
            )
            return filtered_data

        for passdata in data:
            if (hasattr(passdata, 'transform_rules')):
                check_output = self.check_transformation(passdata)
                if (check_output):
                    filtered_data.append(check_output)

        return filtered_data


class PCLOutputIsOk(FilterTemplate):

    def apply(self, data):
        filtered_data = []
        pcl_list = self.variable if (hasattr(self, 'variable')) \
            else data[0].pcl_output.keys()

        for passdata in data:
            for pcl in pcl_list:
                if (passdata.getPCLOutput(pcl) == "OK"):
                    filtered_data.append(passdata)
                    break

        return filtered_data


class PCLOutputIsNotOk(FilterTemplate):

    def apply(self, data):
        filtered_data = []
        pcl_list = self.variable if (hasattr(self, 'variable')) \
            else data[0].pcl_output.keys()

        for passdata in data:
            for pcl in pcl_list:
                if (passdata.getPCLOutput(pcl) != "OK"):
                    filtered_data.append(passdata)
                    break

        return filtered_data


class HigherScoreThan(FilterTemplate):

    def apply(self, data):
        keyErrors = []
        high_score_data = []

        for passdata in data:
            for pcl, threshold in self.variable.items():
                try:
                    pcl_score = passdata.getPCLScore(pcl)
                    if (pcl_score and int(pcl_score) >= threshold):
                        high_score_data.append(passdata)
                        break
                except KeyError:
                    if (pcl not in keyErrors):
                        errorPrinter.printWarning(
                            self.__class__.__name__,
                            "Key \'" + pcl + "\' does not exist."
                        )
                        keyErrors.append(pcl)

            # Remove undefined keys from dictionary before next iteration
            for keyError in keyErrors:
                self.variable.pop(keyError, None)

        return high_score_data


class LowerScoreThan(FilterTemplate):

    def apply(self, data):
        keyErrors = []
        low_score_data = []

        for passdata in data:
            for pcl, threshold in self.variable.items():
                try:
                    pcl_score = passdata.getPCLScore(pcl)
                    if (pcl_score and int(pcl_score) < threshold):
                        low_score_data.append(passdata)
                        break
                except KeyError:
                    if (pcl not in keyErrors):
                        errorPrinter.printWarning(
                            self.__class__.__name__,
                            "Key \'" + pcl + "\' does not exist."
                        )
                        keyErrors.append(pcl)

            # Remove undefined keys from dictionary before next iteration
            for keyError in keyErrors:
                self.variable.pop(keyError, None)

        return low_score_data


class ChangePCLOutputByScore(FilterTemplate):

    def apply(self, data):
        keyErrors = []

        for passdata in data:
            for pcl, threshold in self.variable.items():
                try:
                    pcl_score = passdata.getPCLScore(pcl)
                    if (pcl_score and int(pcl_score) < threshold):
                        if (passdata.getPCLOutput(pcl) == ''):
                            passdata.pcl_output[pcl] = (
                                'Low password score',
                                pcl_score
                            )
                    else:
                        if (not passdata.getPCLOutput(pcl)):
                            passdata.pcl_output[pcl] = (
                                "OK",
                                pcl_score
                            )
                except KeyError:
                    if (pcl not in keyErrors):
                        errorPrinter.printWarning(
                            self.__class__.__name__,
                            "Key \'" + pcl + "\' does not exist."
                        )
                        keyErrors.append(pcl)

            # Remove undefined keys from dictionary before next iteration
            for keyError in keyErrors:
                self.variable.pop(keyError, None)

        return data
