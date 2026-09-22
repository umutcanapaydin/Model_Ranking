import SwiftUI

/// Adaptive surfaces shared by home, ranking and evidence. No product facts live here.
enum Design {
    static let canvas = adaptive(light: 0xF5F4EE, dark: 0x151D1B)
    static let paper = adaptive(light: 0xFFFFFF, dark: 0x202C28)
    static let ink = adaptive(light: 0x203B32, dark: 0xE9F0E8)
    static let accent = adaptive(light: 0x285A46, dark: 0xB9D7A7)
    static let muted = adaptive(light: 0x68776F, dark: 0xADBCB3)
    static let line = adaptive(light: 0xE2E7DE, dark: 0x35433D)
    static let forest = Color(red: 0.10, green: 0.23, blue: 0.18)
    static let lime = Color(red: 0.82, green: 0.91, blue: 0.65)

    private static func adaptive(light: UInt32, dark: UInt32) -> Color {
        Color(uiColor: UIColor { traits in
            let hex = traits.userInterfaceStyle == .dark ? dark : light
            return UIColor(
                red: CGFloat((hex >> 16) & 255) / 255,
                green: CGFloat((hex >> 8) & 255) / 255,
                blue: CGFloat(hex & 255) / 255, alpha: 1
            )
        })
    }
}

struct ModelMark: View {
    let vendor: String
    var prominent = false

    var body: some View {
        Text(String(vendor.prefix(1)).uppercased())
            .font(.system(.title3, design: .serif).weight(.semibold))
            .frame(width: 42, height: 42)
            .foregroundStyle(prominent ? Design.lime : Design.accent)
            .background(prominent ? Color.white.opacity(0.10) : Design.accent.opacity(0.08))
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .accessibilityHidden(true)
    }
}
