"""
Security Vulnerability Scanner
Performs automated security scanning and compliance checks
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime


class VulnerabilityScanner:
    """Automated vulnerability scanning"""
    
    def __init__(self, project_root=None):
        self.project_root = project_root or Path.cwd()
        self.results = {}
    
    def check_dependencies(self):
        """Check for vulnerable dependencies using Safety"""
        print("[*] Checking dependencies with Safety...")
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            try:
                vulns = json.loads(result.stdout) if result.stdout else []
                self.results['dependencies'] = {
                    'vulnerabilities': vulns,
                    'vulnerable_packages': len([v for v in vulns if v.get('vulnerability')]),
                    'status': 'PASS' if not vulns else 'FAIL'
                }
            except json.JSONDecodeError:
                self.results['dependencies'] = {'status': 'ERROR', 'message': 'Failed to parse Safety output'}
        except FileNotFoundError:
            self.results['dependencies'] = {'status': 'SKIPPED', 'reason': 'Safety not installed'}
        except subprocess.TimeoutExpired:
            self.results['dependencies'] = {'status': 'TIMEOUT'}
    
    def check_code_security(self):
        """Check code for security issues using Bandit"""
        print("[*] Scanning code with Bandit...")
        try:
            result = subprocess.run(
                ['bandit', '-r', '.', '-f', 'json', '--ll'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            try:
                data = json.loads(result.stdout) if result.stdout else {}
                issues = data.get('results', [])
                self.results['code_security'] = {
                    'issues': issues,
                    'critical_count': len([i for i in issues if i.get('severity') == 'HIGH']),
                    'high_count': len([i for i in issues if i.get('severity') == 'MEDIUM']),
                    'status': 'PASS' if not issues else 'FAIL'
                }
            except json.JSONDecodeError:
                self.results['code_security'] = {'status': 'ERROR', 'message': 'Failed to parse Bandit output'}
        except FileNotFoundError:
            self.results['code_security'] = {'status': 'SKIPPED', 'reason': 'Bandit not installed'}
        except subprocess.TimeoutExpired:
            self.results['code_security'] = {'status': 'TIMEOUT'}
    
    def check_sast(self):
        """Check for SAST issues using Semgrep"""
        print("[*] Running SAST analysis with Semgrep...")
        try:
            result = subprocess.run(
                ['semgrep', '--config=p/security-audit', '--json', '.'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            try:
                data = json.loads(result.stdout) if result.stdout else {}
                issues = data.get('results', [])
                self.results['sast'] = {
                    'issues': issues,
                    'count': len(issues),
                    'status': 'PASS' if not issues else 'FAIL'
                }
            except json.JSONDecodeError:
                self.results['sast'] = {'status': 'SKIPPED', 'reason': 'Failed to parse output'}
        except FileNotFoundError:
            self.results['sast'] = {'status': 'SKIPPED', 'reason': 'Semgrep not installed'}
        except subprocess.TimeoutExpired:
            self.results['sast'] = {'status': 'TIMEOUT'}
    
    def check_container_security(self):
        """Check container image security using Trivy"""
        print("[*] Scanning container with Trivy...")
        try:
            # Assume image name is ceng302-middleware
            result = subprocess.run(
                ['trivy', 'image', '--json', 'ceng302-middleware'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            try:
                data = json.loads(result.stdout) if result.stdout else {}
                vulnerabilities = []
                for result_item in data.get('Results', []):
                    vulns = result_item.get('Vulnerabilities', [])
                    vulnerabilities.extend(vulns)
                
                self.results['container'] = {
                    'vulnerabilities': vulnerable,
                    'critical_count': len([v for v in vulnerabilities if v.get('Severity') == 'CRITICAL']),
                    'high_count': len([v for v in vulnerabilities if v.get('Severity') == 'HIGH']),
                    'status': 'PASS' if not vulnerabilities else 'FAIL'
                }
            except json.JSONDecodeError:
                self.results['container'] = {'status': 'SKIPPED'}
        except FileNotFoundError:
            self.results['container'] = {'status': 'SKIPPED', 'reason': 'Trivy not installed'}
        except subprocess.TimeoutExpired:
            self.results['container'] = {'status': 'TIMEOUT'}
    
    def check_secrets(self):
        """Check for exposed secrets using detect-secrets"""
        print("[*] Scanning for exposed secrets...")
        try:
            result = subprocess.run(
                ['detect-secrets', 'scan', '--json', '--all-files'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            try:
                data = json.loads(result.stdout) if result.stdout else {}
                results = data.get('results', {})
                secret_count = sum(len(v) for v in results.values())
                
                self.results['secrets'] = {
                    'exposed_secrets': secret_count,
                    'files_with_secrets': list(results.keys()),
                    'status': 'PASS' if secret_count == 0 else 'FAIL'
                }
            except json.JSONDecodeError:
                self.results['secrets'] = {'status': 'ERROR'}
        except FileNotFoundError:
            self.results['secrets'] = {'status': 'SKIPPED', 'reason': 'detect-secrets not installed'}
        except subprocess.TimeoutExpired:
            self.results['secrets'] = {'status': 'TIMEOUT'}
    
    def check_compliance(self):
        """Check for compliance issues"""
        print("[*] Checking compliance...")
        
        requirements_file = self.project_root / 'requirements_middleware.txt'
        compliance_issues = []
        
        if requirements_file.exists():
            with open(requirements_file) as f:
                for line in f:
                    # Check for packages with known vulnerabilities
                    if 'django' in line and '<3.2.10' in line:
                        compliance_issues.append({
                            'package': 'Django',
                            'issue': 'Known vulnerabilities in version < 3.2.10',
                            'severity': 'HIGH'
                        })
        
        self.results['compliance'] = {
            'issues': compliance_issues,
            'status': 'PASS' if not compliance_issues else 'FAIL'
        }
    
    def run_all_scans(self):
        """Run all vulnerability scans"""
        print("\n" + "="*60)
        print("🔒 SECURITY VULNERABILITY SCANNER")
        print("="*60 + "\n")
        
        self.check_dependencies()
        self.check_code_security()
        self.check_sast()
        self.check_container_security()
        self.check_secrets()
        self.check_compliance()
        
        return self.get_report()
    
    def get_report(self):
        """Generate vulnerability scan report"""
        report = {
            'scan_timestamp': datetime.utcnow().isoformat(),
            'project_root': str(self.project_root),
            'results': self.results,
            'summary': self._calculate_summary()
        }
        return report
    
    def _calculate_summary(self):
        """Calculate overall security score"""
        checks = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get('status') == 'PASS')
        
        security_score = (passed / checks * 100) if checks > 0 else 0
        
        overall_vulnerabilities = 0
        for result in self.results.values():
            overall_vulnerabilities += result.get('critical_count', 0) * 3
            overall_vulnerabilities += result.get('high_count', 0) * 1
        
        return {
            'total_checks': checks,
            'passed_checks': passed,
            'security_score': round(security_score, 1),
            'critical_vulnerabilities': sum(r.get('critical_count', 0) for r in self.results.values()),
            'high_vulnerabilities': sum(r.get('high_count', 0) for r in self.results.values()),
            'risk_level': self._get_risk_level(security_score)
        }
    
    @staticmethod
    def _get_risk_level(score):
        """Determine risk level based on score"""
        if score >= 90:
            return 'LOW'
        elif score >= 70:
            return 'MEDIUM'
        elif score >= 50:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    def export_report(self, filename=None):
        """Export scan report to JSON file"""
        if filename is None:
            filename = f"security_scan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = self.get_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report exported to {filename}")
        return filename
    
    def print_report(self):
        """Print scan report to console"""
        report = self.get_report()
        summary = report['summary']
        
        print("\n" + "="*60)
        print("📊 VULNERABILITY SCAN REPORT")
        print("="*60)
        print(f"\nTimestamp: {report['scan_timestamp']}")
        print(f"Project: {report['project_root']}")
        print(f"\n🎯 SECURITY SCORE: {summary['security_score']}/100 ({summary['risk_level']} RISK)")
        print(f"   Passed: {summary['passed_checks']}/{summary['total_checks']}")
        print(f"   Critical Vulnerabilities: {summary['critical_vulnerabilities']}")
        print(f"   High Vulnerabilities: {summary['high_vulnerabilities']}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for check_name, result in report['results'].items():
            status = result.get('status', 'UNKNOWN')
            symbol = '✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⏭️'
            print(f"   {symbol} {check_name}: {status}")
        
        print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    scanner = VulnerabilityScanner()
    scanner.run_all_scans()
    scanner.print_report()
    scanner.export_report()
