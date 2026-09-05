import Link from "next/link";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import styles from "@/components/research/WorkspaceState.module.css";
export default function NotFound() { return <section className={styles.state}><span className={styles.icon}><WorkspaceIcon name="search" /></span><h1>찾는 화면이 없습니다</h1><p>주소가 변경되었거나 아직 연결되지 않은 자료입니다. 전체 메뉴에서 다른 화면을 찾아보세요.</p><div className={styles.actions}><Link href="/">리서치 홈으로</Link><Link href="/recommendations">투자 후보 보기</Link></div></section>; }
