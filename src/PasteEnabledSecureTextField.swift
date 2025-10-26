import Cocoa

final class PasteEnabledSecureTextField: NSSecureTextField {
    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        guard event.type == .keyDown else {
            return super.performKeyEquivalent(with: event)
        }

        let modifiers = event.modifierFlags.intersection(.deviceIndependentFlagsMask)
        guard modifiers.contains(.command), let characters = event.charactersIgnoringModifiers?.lowercased() else {
            return super.performKeyEquivalent(with: event)
        }

        switch characters {
        case "v":
            if NSApp.sendAction(#selector(NSText.paste(_:)), to: nil, from: self) {
                return true
            }
        case "c":
            if NSApp.sendAction(#selector(NSText.copy(_:)), to: nil, from: self) {
                return true
            }
        case "x":
            if NSApp.sendAction(#selector(NSText.cut(_:)), to: nil, from: self) {
                return true
            }
        case "a":
            if NSApp.sendAction(#selector(NSText.selectAll(_:)), to: nil, from: self) {
                return true
            }
        default:
            break
        }

        return super.performKeyEquivalent(with: event)
    }
}
