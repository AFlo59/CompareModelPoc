"""
Tests additionnels pour src.analytics.system_monitoring
"""

import os
import sys
from unittest.mock import Mock, patch

import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSystemMonitoringAdditional:
    def test_get_disk_stats_permission_error(self):
        from src.analytics import system_monitoring as sm

        class Part:
            device = 'd'
            mountpoint = '/mnt/x'
            fstype = 'ext4'

        with patch.object(sm.psutil, 'disk_partitions', return_value=[Part()]), \
             patch.object(sm.psutil, 'disk_usage', side_effect=PermissionError):
            res = sm.get_disk_stats()
            # PermissionError doit être ignoré (continue)
            assert isinstance(res, list) and len(res) == 0

    def test_format_bytes_reaches_pb(self):
        from src.analytics.system_monitoring import format_bytes
        # Nombre suffisamment grand pour dépasser TB
        val = 1024.0 ** 6  # 1 PB
        s = format_bytes(val)
        assert 'PB' in s

    def test_create_disk_chart_empty(self):
        from src.analytics.system_monitoring import create_disk_chart
        fig = create_disk_chart([])
        assert isinstance(fig, go.Figure)

    @patch('src.analytics.system_monitoring.st')
    def test_show_system_monitoring_refresh_and_auto(self, mock_st):
        from src.analytics.system_monitoring import show_system_monitoring

        # Préparer stats minimales
        mock_st.columns.side_effect = lambda spec: [Mock(__enter__=Mock(return_value=Mock()), __exit__=Mock(return_value=None)) for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.expander.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.expander.return_value.__exit__ = Mock(return_value=None)
        mock_st.button.side_effect = lambda label, **kw: 'Actualiser' in label
        mock_st.checkbox.return_value = True

        with patch('src.analytics.system_monitoring.get_system_info', return_value={
            'os': 'X', 'os_version': '1', 'architecture': 'x64', 'processor': 'p', 'python_version': '3', 'cpu_count': 1, 'cpu_count_logical': 2, 'boot_time': __import__('datetime').datetime.now()
        }), \
             patch('src.analytics.system_monitoring.get_cpu_stats', return_value={'cpu_usage_total': 0.0, 'cpu_usage_per_core': [0], 'cpu_frequency_current': 0, 'cpu_frequency_max': 0, 'load_average': [0,0,0]}), \
             patch('src.analytics.system_monitoring.get_memory_stats', return_value={'memory_total': 1, 'memory_available': 1, 'memory_used': 0, 'memory_percent': 0.0, 'swap_total': 0, 'swap_used': 0, 'swap_percent': 0.0}), \
             patch('src.analytics.system_monitoring.get_disk_stats', return_value=[]), \
             patch('src.analytics.system_monitoring.get_network_stats', return_value={'bytes_recv':0,'packets_recv':0,'errin':0,'dropin':0,'bytes_sent':0,'packets_sent':0,'errout':0,'dropout':0}), \
             patch('src.analytics.system_monitoring.get_streamlit_process_info', return_value={'pid':1,'memory_info':type('mi',(),{'rss':0,'vms':0})(),'cpu_percent':0.0,'create_time': __import__('datetime').datetime.now(),'status':'running','num_threads':1}), \
             patch('time.sleep', return_value=None):
            show_system_monitoring()
        # Auto refresh coche -> sleep + rerun, et bouton Actualiser -> rerun
        assert mock_st.rerun.called


