interface CloudRailLogoProps {
  className?: string
  size?: number
}

export default function CloudRailLogo({ className = '', size = 32 }: CloudRailLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Cloud */}
      <path
        d="M25 45C25 38.3726 30.3726 33 37 33C38.3065 33 39.5617 33.2346 40.7241 33.6648C42.8939 27.6793 48.7911 23.5 55.5 23.5C64.0604 23.5 71 30.4396 71 39C71 39.6716 70.9584 40.3334 70.8779 40.9832C76.0815 42.2718 80 46.9615 80 52.5C80 59.1274 74.6274 64.5 68 64.5H32C25.3726 64.5 20 59.1274 20 52.5C20 48.134 22.6863 44.3743 26.5 42.6104C25.5346 41.5267 25 40.0899 25 38.5C25 35.4624 27.4624 33 30.5 33C31.0909 33 31.6559 33.1071 32.1767 33.3022C29.5678 35.5134 28 38.6667 28 42.1667C28 43.2712 28.1364 44.3438 28.3928 45.3667C26.9815 46.2834 25.8333 47.5833 25 49.0833V45Z"
        fill="currentColor"
        opacity="0.9"
      />

      {/* Rail - three horizontal lines */}
      <rect x="15" y="72" width="70" height="4" rx="2" fill="currentColor" />
      <rect x="15" y="80" width="70" height="3" rx="1.5" fill="currentColor" opacity="0.6" />
      <rect x="20" y="87" width="60" height="2" rx="1" fill="currentColor" opacity="0.4" />

      {/* Rail connectors (vertical lines) */}
      <rect x="25" y="72" width="2" height="15" fill="currentColor" opacity="0.3" />
      <rect x="48" y="72" width="2" height="15" fill="currentColor" opacity="0.3" />
      <rect x="73" y="72" width="2" height="15" fill="currentColor" opacity="0.3" />
    </svg>
  )
}
