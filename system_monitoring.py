import platform
import queue
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st


def get_system_info() -> Dict:
    """Récupère les informations système de base."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()),
    }


def get_cpu_stats() -> Dict:
    """Récupère les statistiques CPU."""
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    cpu_freq = psutil.cpu_freq()

    return {
        "cpu_usage_total": psutil.cpu_percent(interval=0.1),
        "cpu_usage_per_core": cpu_percent,
        "cpu_frequency_current": cpu_freq.current if cpu_freq else 0,
        "cpu_frequency_max": cpu_freq.max if cpu_freq else 0,
        "load_average": psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0, 0, 0],
    }


def get_memory_stats() -> Dict:
    """Récupère les statistiques mémoire."""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "memory_total": memory.total,
        "memory_available": memory.available,
        "memory_used": memory.used,
        "memory_percent": memory.percent,
        "swap_total": swap.total,
        "swap_used": swap.used,
        "swap_percent": swap.percent,
    }


def get_disk_stats() -> List[Dict]:
    """Récupère les statistiques disque."""
    disk_stats = []
    partitions = psutil.disk_partitions()

    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_stats.append(
                {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0,
                }
            )
        except PermissionError:
            continue

    return disk_stats


def get_network_stats() -> Dict:
    """Récupère les statistiques réseau."""
    net_io = psutil.net_io_counters()

    return {
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
        "errin": net_io.errin,
        "errout": net_io.errout,
        "dropin": net_io.dropin,
        "dropout": net_io.dropout,
    }


def get_streamlit_process_info() -> Dict:
    """Récupère les informations sur le processus Streamlit actuel."""
    import os

    current_process = psutil.Process(os.getpid())

    return {
        "pid": current_process.pid,
        "memory_info": current_process.memory_info(),
        "cpu_percent": current_process.cpu_percent(),
        "create_time": datetime.fromtimestamp(current_process.create_time()),
        "status": current_process.status(),
        "num_threads": current_process.num_threads(),
    }


def format_bytes(bytes_value: int) -> str:
    """Formate les bytes en unités lisibles."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def create_cpu_chart(cpu_stats: Dict) -> go.Figure:
    """Crée un graphique d'utilisation CPU."""
    fig = go.Figure()

    # Graphique global
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=cpu_stats["cpu_usage_total"],
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "CPU Global (%)"},
            gauge={
                "axis": {"range": [None, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "lightgray"},
                    {"range": [50, 80], "color": "yellow"},
                    {"range": [80, 100], "color": "red"},
                ],
                "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
            },
        )
    )

    fig.update_layout(height=300)
    return fig


def create_memory_chart(memory_stats: Dict) -> go.Figure:
    """Crée un graphique d'utilisation mémoire."""
    labels = ["Utilisée", "Disponible"]
    values = [memory_stats["memory_used"], memory_stats["memory_available"]]
    colors = ["#ff6b6b", "#51cf66"]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors, hole=0.5)])

    fig.update_layout(title=f"Mémoire RAM - {memory_stats['memory_percent']:.1f}% utilisée", height=300, showlegend=True)

    return fig


def create_disk_chart(disk_stats: List[Dict]) -> go.Figure:
    """Crée un graphique d'utilisation disque."""
    if not disk_stats:
        return go.Figure()

    devices = [disk["device"] for disk in disk_stats]
    used_percentages = [disk["percent"] for disk in disk_stats]

    colors = ["red" if p > 80 else "orange" if p > 60 else "green" for p in used_percentages]

    fig = go.Figure(
        data=[
            go.Bar(
                x=devices,
                y=used_percentages,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in used_percentages],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Utilisation des disques (%)",
        xaxis_title="Périphériques",
        yaxis_title="Utilisation (%)",
        yaxis=dict(range=[0, 100]),
        height=300,
    )

    return fig


def show_system_monitoring():
    """Affiche le monitoring système complet."""
    st.title("🖥️ Monitoring Système")

    # Bouton de rafraîchissement
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Actualiser", type="primary"):
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)

    if auto_refresh:
        time.sleep(30)
        st.rerun()

    # Informations système de base
    with st.expander("ℹ️ Informations Système", expanded=False):
        sys_info = get_system_info()
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
            **Système d'exploitation :** {sys_info['os']} {sys_info['os_version']}  
            **Architecture :** {sys_info['architecture']}  
            **Processeur :** {sys_info['processor'][:50]}...  
            """
            )

        with col2:
            st.markdown(
                f"""
            **Python :** {sys_info['python_version']}  
            **CPU Cores :** {sys_info['cpu_count']} physiques, {sys_info['cpu_count_logical']} logiques  
            **Démarrage :** {sys_info['boot_time'].strftime('%Y-%m-%d %H:%M:%S')}  
            """
            )

    # Métriques en temps réel
    cpu_stats = get_cpu_stats()
    memory_stats = get_memory_stats()
    disk_stats = get_disk_stats()
    network_stats = get_network_stats()
    process_info = get_streamlit_process_info()

    # Métriques principales
    st.markdown("### 📊 Métriques Principales")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💻 CPU Global", f"{cpu_stats['cpu_usage_total']:.1f}%", delta=None)

    with col2:
        st.metric(
            "🧠 RAM",
            f"{memory_stats['memory_percent']:.1f}%",
            delta=f"-{format_bytes(memory_stats['memory_available'])} libre",
        )

    with col3:
        if disk_stats:
            avg_disk = sum(d["percent"] for d in disk_stats) / len(disk_stats)
            st.metric("💾 Disque Moyen", f"{avg_disk:.1f}%")
        else:
            st.metric("💾 Disque", "N/A")

    with col4:
        st.metric("📱 App CPU", f"{process_info['cpu_percent']:.1f}%", delta=f"{process_info['num_threads']} threads")

    # Graphiques détaillés
    st.markdown("### 📈 Graphiques Détaillés")

    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(create_cpu_chart(cpu_stats), use_container_width=True)

    with col2:
        st.plotly_chart(create_memory_chart(memory_stats), use_container_width=True)

    # Graphique des disques
    if disk_stats:
        st.plotly_chart(create_disk_chart(disk_stats), use_container_width=True)

    # Détails par coeur CPU
    with st.expander("🔧 Détails CPU par coeur", expanded=False):
        cpu_cores_df = pd.DataFrame(
            {
                "Coeur": [f"CPU {i}" for i in range(len(cpu_stats["cpu_usage_per_core"]))],
                "Utilisation (%)": cpu_stats["cpu_usage_per_core"],
            }
        )

        fig = px.bar(
            cpu_cores_df,
            x="Coeur",
            y="Utilisation (%)",
            color="Utilisation (%)",
            color_continuous_scale="Viridis",
            title="Utilisation par coeur CPU",
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Détails mémoire
    with st.expander("💾 Détails Mémoire et Stockage", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Mémoire RAM :**")
            st.markdown(f"- Total : {format_bytes(memory_stats['memory_total'])}")
            st.markdown(f"- Utilisée : {format_bytes(memory_stats['memory_used'])}")
            st.markdown(f"- Disponible : {format_bytes(memory_stats['memory_available'])}")

            if memory_stats["swap_total"] > 0:
                st.markdown("**Mémoire Swap :**")
                st.markdown(f"- Total : {format_bytes(memory_stats['swap_total'])}")
                st.markdown(f"- Utilisée : {format_bytes(memory_stats['swap_used'])} ({memory_stats['swap_percent']:.1f}%)")

        with col2:
            if disk_stats:
                st.markdown("**Stockage :**")
                for disk in disk_stats:
                    st.markdown(f"**{disk['device']}** ({disk['mountpoint']})")
                    st.markdown(f"- Total : {format_bytes(disk['total'])}")
                    st.markdown(f"- Utilisé : {format_bytes(disk['used'])} ({disk['percent']:.1f}%)")
                    st.markdown(f"- Libre : {format_bytes(disk['free'])}")
                    st.markdown("---")

    # Informations réseau
    with st.expander("🌐 Statistiques Réseau", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Trafic Entrant :**")
            st.markdown(f"- Bytes reçus : {format_bytes(network_stats['bytes_recv'])}")
            st.markdown(f"- Paquets reçus : {network_stats['packets_recv']:,}")
            st.markdown(f"- Erreurs : {network_stats['errin']:,}")
            st.markdown(f"- Drops : {network_stats['dropin']:,}")

        with col2:
            st.markdown("**Trafic Sortant :**")
            st.markdown(f"- Bytes envoyés : {format_bytes(network_stats['bytes_sent'])}")
            st.markdown(f"- Paquets envoyés : {network_stats['packets_sent']:,}")
            st.markdown(f"- Erreurs : {network_stats['errout']:,}")
            st.markdown(f"- Drops : {network_stats['dropout']:,}")

    # Informations sur l'application
    with st.expander("🚀 Informations Application Streamlit", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**PID :** {process_info['pid']}")
            st.markdown(f"**Status :** {process_info['status']}")
            st.markdown(f"**Threads :** {process_info['num_threads']}")
            st.markdown(f"**Démarré :** {process_info['create_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        with col2:
            st.markdown(f"**Mémoire RSS :** {format_bytes(process_info['memory_info'].rss)}")
            st.markdown(f"**Mémoire VMS :** {format_bytes(process_info['memory_info'].vms)}")
            st.markdown(f"**CPU Usage :** {process_info['cpu_percent']:.1f}%")

            uptime = datetime.now() - process_info["create_time"]
            st.markdown(f"**Uptime :** {str(uptime).split('.')[0]}")


if __name__ == "__main__":
    show_system_monitoring()
